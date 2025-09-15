import os
from typing import Optional, List, Dict, Any, Sequence, Tuple, Union
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import patches
from matplotlib import font_manager as fm
import seaborn as sns
import joblib
import base64
import io
from redis_utils import get_redis

ArrayLike = Union[np.ndarray, pd.DataFrame, Sequence[Sequence[float]]]

# ---------- Helper: reduce background samples ----------

def reduce_background_umap_samples(
    background_umap_csv: str,
    samples_per_class: Optional[int] = 500,
    random_state: Optional[int] = 42,
    strategy: str = 'uniform'
) -> pd.DataFrame:
    df = pd.read_csv(background_umap_csv)
    original_count = len(df)
    
    # If samples_per_class is None, return all samples
    if samples_per_class is None:
        print(f"Using all background samples: {original_count}")
        return df
    
    if 'class' in df.columns:
        unique_classes = df['class'].unique()
        n_classes = len(unique_classes)
        
        if strategy == 'uniform':
            # Equal samples per class (this is the main use case now)
            reduced_dfs = []
            total_sampled = 0
            for class_name in unique_classes:
                class_data = df[df['class'] == class_name]
                if len(class_data) > samples_per_class:
                    sampled = class_data.sample(n=samples_per_class, random_state=random_state)
                else:
                    sampled = class_data
                reduced_dfs.append(sampled)
                total_sampled += len(sampled)
            reduced_df = pd.concat(reduced_dfs, ignore_index=True)
            # print(f"Reduced background samples: {original_count} → {total_sampled} ({samples_per_class} per class × {n_classes} classes)")
        
        else:  # stratified
            # Proportional samples per class (legacy mode)
            total_target = samples_per_class * n_classes
            reduced_df = df.groupby('class').apply(
                lambda x: x.sample(
                    n=max(1, int(len(x) * total_target / original_count)),
                    random_state=random_state
                )
            ).reset_index(drop=True)
            
            # If still too many, randomly sample to exact target
            if len(reduced_df) > total_target:
                reduced_df = reduced_df.sample(n=total_target, random_state=random_state)
            # print(f"Reduced background samples: {original_count} → {len(reduced_df)} (stratified sampling)")
    else:
        # No class column, just random sample
        total_target = samples_per_class if samples_per_class else original_count
        if original_count > total_target:
            reduced_df = df.sample(n=total_target, random_state=random_state)
            # print(f"Reduced background samples: {original_count} → {total_target} (no class info)")
        else:
            reduced_df = df
            # print(f"Using all background samples: {original_count} (no reduction needed)")
    
    return reduced_df

# ---------- Core: sampling + smoothing ----------

def sample_and_smooth_embeddings(
    inputdata: pd.DataFrame,
    raw_embedding: pd.DataFrame,
    feature_cols: List[str],
    *,
    sample_size: int = 1,
    random_state: Optional[int] = None,
    input_class_col: str = "prompt",
    bg_class_col: str = "class",
) -> Dict[str, Any]:
    """
    Sample and smooth embeddings for user input data.
    """
    if input_class_col not in inputdata.columns:
        raise KeyError(f"`input_class_col='{input_class_col}'` not found in inputdata.")
    if bg_class_col not in raw_embedding.columns:
        raise KeyError(f"`bg_class_col='{bg_class_col}'` not found in raw_embedding.")
    for c in feature_cols:
        if c not in inputdata.columns:
            raise KeyError(f"inputdata missing column: {c}")
        if c not in raw_embedding.columns:
            raise KeyError(f"raw_embedding missing column: {c}")

    rng = np.random.default_rng(random_state) if random_state is not None else None

    results, skipped = [], []
    for _, row in inputdata.iterrows():
        cls = row[input_class_col]
        candidates = raw_embedding[raw_embedding[bg_class_col] == cls]
        if len(candidates) == 0:
            skipped.append(cls)
            continue

        seed = int(rng.integers(0, 2**32 - 1)) if rng is not None else None
        sampled = candidates.sample(
            n=min(sample_size, len(candidates)),
            replace=(len(candidates) < sample_size),
            random_state=seed
        )

        sampled_avg = sampled[[*feature_cols]].mean(axis=0).values
        input_vec = row[[*feature_cols]].values
        final_vec = (sampled_avg * sample_size + input_vec) / (sample_size + 1)

        results.append({input_class_col: cls, "final_emb": final_vec})

    if len(results) == 0:
        mix_df = pd.DataFrame(columns=[input_class_col] + feature_cols)
    else:
        mix_df = pd.DataFrame([r["final_emb"] for r in results], columns=feature_cols)
        mix_df.insert(0, input_class_col, [r[input_class_col] for r in results])

    return {"mix_df": mix_df, "skipped_classes": skipped}

# ---------- Helper: scale fitting / application ----------

def _fit_linear_scale(src: np.ndarray, dst: np.ndarray) -> Tuple[float, float]:
    """
    Fit linear:  dst ≈ m * src + c  (least squares)
    Returns (m, c).
    """
    if len(src) != len(dst) or len(src) < 2:
        raise ValueError("Need >=2 paired points to fit linear scale.")
    m, c = np.polyfit(src, dst, deg=1)
    return float(m), float(c)

def _apply_linear_scale(x: np.ndarray, m: float, c: float) -> np.ndarray:
    return m * x + c

# ---------- Plotting helper functions ----------

def create_plot_with_border(
    background_data: pd.DataFrame,
    user_data: pd.DataFrame,
    x_col: str,
    y_col: str,
    cluster_col: str,
    fixed_palette: Dict[int, str],
    figsize: Tuple[float, float],
    background_size: int,
    background_alpha: float,
    user_marker: str,
    user_color: str,
    user_size: int,
    title: str,
    font_prop: Optional[object] = None,
) -> plt.Figure:
    """
    Create a properly centered plot with white border that won't be cut off.
    """
    # Create figure with proper spacing for border
    fig = plt.figure(figsize=figsize)
    
    # Add subplot with margins to accommodate border
    ax = fig.add_subplot(111)
    
    # Set background color to white
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    # Plot background points
    if cluster_col in background_data.columns:
        sns.scatterplot(
            data=background_data,
            x=x_col, y=y_col,
            hue=cluster_col,
            s=background_size, 
            alpha=background_alpha,
            palette=fixed_palette,
            linewidth=0.5,
            edgecolor="white",
            ax=ax
        )
    else:
        sns.scatterplot(
            data=background_data,
            x=x_col, y=y_col,
            color="#999999",
            s=background_size, 
            alpha=background_alpha,
            linewidth=0,
            ax=ax
        )

    # Plot user points
    sns.scatterplot(
        data=user_data,
        x=x_col, y=y_col,
        marker=user_marker,
        color=user_color,
        s=user_size, 
        alpha=1,
        label="混合樣本",
        ax=ax
    )

    # Set title with proper font
    ax.set_title(title, fontproperties=font_prop, fontsize=17, fontweight="bold", pad=20)
    
    # Remove legend and axis
    if ax.get_legend():
        ax.get_legend().remove()
    ax.axis("off")
    
    # Get the actual data limits to ensure border encompasses everything
    ax.autoscale_view(tight=True)
    
    # Add white border around the entire plot area with proper margins
    # Use figure coordinates to ensure border is always visible
    border = patches.Rectangle(
        (0.02, 0.02), 0.96, 0.96,  # Leave 2% margin on all sides
        transform=fig.transFigure,
        linewidth=3, 
        edgecolor="black", 
        facecolor="none",
        zorder=1000  # Ensure border is on top
    )
    fig.patches.append(border)
    
    return fig

def add_text_annotations(
    ax: plt.Axes,
    user_data: pd.DataFrame,
    x_col: str,
    y_col: str,
    label_dx: float,
    label_dy: float,
    label_fontsize: int,
    font_prop: Optional[object] = None
) -> None:
    """
    Add text annotations for user points.
    """
    if len(user_data) > 0:
        for _, row in user_data.iterrows():
            ax.text(
                row[x_col] + label_dx,
                row[y_col] + label_dy,
                str(row.get("label", "")),
                fontproperties=font_prop,
                fontsize=label_fontsize,
                color="black",
                ha="left", va="bottom",
                bbox=dict(
                    facecolor="white", 
                    alpha=0.8, 
                    edgecolor="gray",
                    linewidth=0.5,
                    pad=2.0
                ),
                zorder=1001  # Above everything else
            )

def save_plot_to_redis(
    fig: plt.Figure,
    redis_key: str,
    dpi: int = 200,
    expire_sec: int = 3600
) -> str:
    """
    Save plot to Redis as base64 encoded image.
    
    Args:
        fig: Matplotlib figure
        redis_key: Redis key to store the image
        dpi: DPI for the saved image
        expire_sec: Expiration time in seconds
    
    Returns:
        base64 encoded image string
    """
    # Save figure to bytes buffer
    buffer = io.BytesIO()
    fig.savefig(
        buffer, 
        format='png',
        dpi=dpi, 
        bbox_inches="tight", 
        pad_inches=0.1,
        facecolor='white',
        edgecolor='none'
    )
    buffer.seek(0)
    
    # Encode to base64
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()
    
    # Store in Redis
    redis_client = get_redis()
    redis_client.set(redis_key, image_base64, ex=expire_sec)
    
    return image_base64

def save_plot_properly(
    fig: plt.Figure,
    output_path: str,
    dpi: int = 200,
    pad_inches: float = 0.1
) -> None:
    """
    Save plot with proper margins to prevent border cutting.
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    
    # Save with slightly more padding to ensure border is visible
    fig.savefig(
        output_path, 
        dpi=dpi, 
        bbox_inches="tight", 
        pad_inches=pad_inches,
        facecolor='white',
        edgecolor='none'
    )

# ---------- Main plotting function ----------

def plot_umap_with_user(
    *,
    raw_embedding_csv: str,         # background embeddings CSV (must have 'class' + emb_*)
    umap_background_csv: str,       # background 2D CSV (must have umap_x, umap_y; optional scale_x, scale_y, class, cluster)
    user_embedding_df: pd.DataFrame,        # user 6 images embeddings dataframe (must have 'prompt' + emb_*)
    umap_reducer_path: str,         # fitted UMAP reducer (.joblib) with .transform()

    # columns
    feature_cols: Optional[List[str]] = None,
    input_class_col: str = "prompt",
    bg_class_col: str = "class",
    cluster_col: str = "cluster",

    # sampling + smoothing
    sample_size: int = 1,
    random_state: Optional[int] = None,
    normalize_class_space: bool = False,  # replace spaces with underscores to align categories
    
    # background reduction
    max_background_samples_per_class: Optional[int] = None,  # e.g., 500 samples per class
    background_sample_strategy: str = 'uniform',  # 'uniform' or 'stratified'

    # scaling to match your "scale_x / scale_y" style
    # Option A: learn from background if it already has scale_x/scale_y;
    # Option B: specify offsets explicitly:
    x_offset: Optional[float] = None,
    x_scale: Optional[float] = None,
    y_offset: Optional[float] = None,
    y_scale: Optional[float] = None,

    # seaborn styling
    figsize: Tuple[float, float] = (10, 7),
    fixed_palette: Optional[Dict[int, str]] = None,   # cluster -> color
    background_size: int = 30,
    background_alpha: float = 0.9,
    user_marker: str = "^",
    user_color: str = "black",
    user_size: int = 120,
    annotate: bool = True,     # e.g., {"soccer_ball":"足球", ...}
    label_fontsize: int = 15,
    label_dx: float = 0.02,
    label_dy: float = 0.02,
    font_path: Optional[str] = None,                  # e.g., NotoSansCJK .ttc

    # output
    output_path: Optional[str] = None,
    redis_key: Optional[str] = None,
    show: bool = False,
) -> Dict[str, Any]:
    # ---- read CSVs ----
    raw_embedding = pd.read_csv(raw_embedding_csv)
    background_Umap = pd.read_csv(umap_background_csv)
    user_embedding = user_embedding_df  # Direct DataFrame instead of CSV
    
    # ---- reduce background samples if requested ----
    if max_background_samples_per_class is not None:
        background_Umap = reduce_background_umap_samples(
            umap_background_csv,
            samples_per_class=max_background_samples_per_class,
            random_state=random_state,
            strategy=background_sample_strategy
        )

    if normalize_class_space:
        if bg_class_col in raw_embedding.columns:
            raw_embedding[bg_class_col] = raw_embedding[bg_class_col].astype(str).str.replace(" ", "_")
        if input_class_col in user_embedding.columns:
            user_embedding[input_class_col] = user_embedding[input_class_col].astype(str).str.replace(" ", "_")
        if "class" in background_Umap.columns:
            background_Umap["class"] = background_Umap["class"].astype(str).str.replace(" ", "_")

    # ---- feature cols ----
    if feature_cols is None:
        feature_cols = [c for c in raw_embedding.columns if c.startswith("emb_")]
        if not feature_cols:
            feature_cols = [c for c in user_embedding.columns if c.startswith("emb_")]
    if not feature_cols:
        raise ValueError("Cannot infer feature_cols (need columns starting with 'emb_').")

    # ---- load reducer ----
    reducer = joblib.load(umap_reducer_path)
    if not hasattr(reducer, "transform"):
        raise ValueError("Loaded UMAP reducer has no `.transform()`.")

    # ---- sampling + smoothing ----
    mix_res = sample_and_smooth_embeddings(
        inputdata=user_embedding,
        raw_embedding=raw_embedding,
        feature_cols=feature_cols,
        sample_size=sample_size,
        random_state=random_state,
        input_class_col=input_class_col,
        bg_class_col=bg_class_col,
    )
    mix_df = mix_res["mix_df"]
    skipped = mix_res["skipped_classes"]

    # ---- project user to 2D ----
    if len(mix_df) > 0:
        user_2d = reducer.transform(mix_df[feature_cols].values)
        mix_df_umap = pd.DataFrame({
            "class": mix_df[input_class_col].values,
            "umap_x": user_2d[:, 0],
            "umap_y": user_2d[:, 1],
        })
    else:
        mix_df_umap = pd.DataFrame(columns=["class", "umap_x", "umap_y"])

    # ---- decide coordinate space (scaled vs raw) ----
    use_scaled = False
    if {"umap_x", "umap_y"}.issubset(background_Umap.columns):
        if {"scale_x", "scale_y"}.issubset(background_Umap.columns):
            # learn per-axis linear mapping
            mx, cx = _fit_linear_scale(background_Umap["umap_x"].values, background_Umap["scale_x"].values)
            my, cy = _fit_linear_scale(background_Umap["umap_y"].values, background_Umap["scale_y"].values)

            background_Umap_plot = background_Umap.copy()
            # apply same mapping to user
            mix_df_umap["scale_x"] = _apply_linear_scale(mix_df_umap["umap_x"].values, mx, cx)
            mix_df_umap["scale_y"] = _apply_linear_scale(mix_df_umap["umap_y"].values, my, cy)
            use_scaled = True

        elif None not in (x_offset, x_scale, y_offset, y_scale):
            # compute scaled for BOTH background and user using explicit params
            background_Umap_plot = background_Umap.copy()
            background_Umap_plot["scale_x"] = (background_Umap_plot["umap_x"] - float(x_offset)) / float(x_scale)
            background_Umap_plot["scale_y"] = (background_Umap_plot["umap_y"] - float(y_offset)) / float(y_scale)

            mix_df_umap["scale_x"] = (mix_df_umap["umap_x"] - float(x_offset)) / float(x_scale)
            mix_df_umap["scale_y"] = (mix_df_umap["umap_y"] - float(y_offset)) / float(y_scale)
            use_scaled = True

        else:
            background_Umap_plot = background_Umap.copy()
    else:
        raise KeyError("`umap_background_csv` must contain 'umap_x' and 'umap_y'.")

    # If not scaled, fall back to raw columns for plotting
    x_col = "scale_x" if use_scaled else "umap_x"
    y_col = "scale_y" if use_scaled else "umap_y"

    # ---- palette ----
    if fixed_palette is None:
        fixed_palette = {
            0: "#1f77b4",  # blue
            1: "#ff7f0e",  # orange
            2: "#2ca02c",  # green
            3: "#fa7d7e",  # red
            4: "#9467bd",  # purple
            5: "#e377c2",  # pink-ish
        }

    # ---- labels (optional mapping, e.g., to Chinese names) ----
    from plot_utils import get_class_label_map
    label_map = get_class_label_map()
    #  --- IGNORE ---
    if label_map is not None and "class" in mix_df_umap.columns:
        mix_df_umap["label"] = mix_df_umap["class"].map(label_map).fillna(mix_df_umap["class"])
    else:
        mix_df_umap["label"] = mix_df_umap.get("class", pd.Series([""] * len(mix_df_umap)))

    # ---- font (optional) ----
    prop = None
    if font_path:
        try:
            prop = fm.FontProperties(fname=font_path)
        except Exception:
            prop = None  # fail silently; fallback to default font

    # ----------- Create and setup the plot -----------
    background_data = background_Umap if not use_scaled else background_Umap_plot
    
    # Create the plot with proper border handling
    fig = create_plot_with_border(
        background_data=background_data,
        user_data=mix_df_umap,
        x_col=x_col,
        y_col=y_col,
        cluster_col=cluster_col,
        fixed_palette=fixed_palette,
        figsize=figsize,
        background_size=background_size,
        background_alpha=background_alpha,
        user_marker=user_marker,
        user_color=user_color,
        user_size=user_size,
        title="我畫的圖與大家畫的圖的距離（標題可改）",
        font_prop=prop
    )
    
    # Get the current axes for text annotations
    ax = fig.gca()
    
    # Add text annotations if requested
    if annotate:
        add_text_annotations(
            ax=ax,
            user_data=mix_df_umap,
            x_col=x_col,
            y_col=y_col,
            label_dx=label_dx,
            label_dy=label_dy,
            label_fontsize=label_fontsize,
            font_prop=prop
        )

    # Save or show the plot
    image_base64 = None
    if redis_key:
        image_base64 = save_plot_to_redis(fig, redis_key)
    
    if output_path:
        save_plot_properly(fig, output_path)

    if show:
        plt.show()
    else:
        plt.close(fig)

    return {
        "user_umap": mix_df_umap,    # includes umap_x/umap_y and possibly scale_x/scale_y + label
        "skipped_classes": skipped,
        "used_scaled": use_scaled,
        "x_col": x_col,
        "y_col": y_col,
        "image_base64": image_base64,  # Add base64 image data
    }

# ---------- Example usage ----------
