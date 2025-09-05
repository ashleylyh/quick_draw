// Category translations (English to Chinese)
export const zhMap = {
    'flashlight': '手電筒', 'belt': '皮帶', 'mushroom': '蘑菇', 'pond': '池塘',
    'strawberry': '草莓', 'pineapple': '鳳梨', 'sun': '太陽', 'cow': '牛',
    'computer': '電腦', 'hot_air_balloon': '熱氣球', 'dog': '狗', 'butterfly': '蝴蝶',
    'bird': '鳥', 'clock': '時鐘', 'star': '星星', 'mountain': '山',
    'bee': '蜜蜂', 'fish': '魚', 'calculator': '計算機', 'see_saw': '翹翹板',
    'bus': '公車', 'octopus': '章魚', 'ice_cream': '冰淇淋', 'car': '汽車',
    'map': '地圖', 'crab': '螃蟹', 'bicycle': '腳踏車', 'tree': '樹',
    'spider': '蜘蛛', 'envelope': '信封', 'eyeglasses': '眼鏡', 'campfire': '營火',
    'ambulance': '救護車'
};

export function toZh(en) {
    return zhMap[en] || en;
}

export function formatTimestamp(ts) {
    if (!ts) return '未知時間';
    
    try {
        // Handle different timestamp formats
        let date;
        if (typeof ts === 'string') {
            // Try parsing as ISO string first
            date = new Date(ts);
        } else if (typeof ts === 'number') {
            // Handle Unix timestamp (in milliseconds or seconds)
            date = new Date(ts > 1000000000000 ? ts : ts * 1000);
        } else {
            return '無效時間格式';
        }
        
        if (isNaN(date.getTime())) {
            console.error('Invalid date:', ts);
            return ts.toString(); // Return original value as fallback
        }
        
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hour = String(date.getHours()).padStart(2, '0');
        const min = String(date.getMinutes()).padStart(2, '0');
        return `${year}-${month}-${day} ${hour}:${min}`;
    } catch (error) {
        console.error('Error formatting timestamp:', error);
        return '時間格式錯誤';
    }
}

export function buildCSVFromData(data) {
    let csv = 'Session ID,Player Name,Gender,Age,Difficulty,Round,Prompt,Time Spent (s),Timed Out,Predictions,Timestamp\n';
    (data.drawings || []).forEach(d => {
        const preds = typeof d.predictions === 'string' ? d.predictions : JSON.stringify(d.predictions || {});
        const row = [
            data.session.session_id, data.session.player_name, data.session.gender, data.session.age,
            data.session.difficulty, d.round, d.prompt, d.time_spent_sec, d.timed_out, `"${preds}"`, d.timestamp
        ].join(',');
        csv += row + '\n';
    });
    return csv;
}

export function parsePredictions(predictions) {
    if (typeof predictions === 'string') {
        try {
            return JSON.parse(predictions);
        } catch {
            return {};
        }
    }
    return predictions || {};
}
