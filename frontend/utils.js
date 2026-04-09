export const zhMap = {
    'fish': '魚',
    'eyeglasses': '眼鏡',
    'camel': '駱駝',
    'see_saw': '翹翹板',
    'bicycle': '腳踏車',
    'shark': '鯊魚',
    'palm_tree': '棕櫚樹',
    'hot_air_balloon': '熱氣球',
    'lollipop': '棒棒糖',
    'mushroom': '蘑菇',
    'umbrella': '雨傘',
    'penguin': '企鵝',
    'tree': '樹',
    'spider': '蜘蛛',
    'octopus': '章魚',
    'hedgehog': '刺蝟',
    'campfire': '營火',
    'crab': '螃蟹',
    'helicopter': '直升機',
    'ambulance': '救護車',
    'police_car': '警車',
    'car': '汽車',
    'truck': '卡車',
    'bus': '公車',
    'radio': '收音機',
    'map': '地圖',
    'envelope': '信封',
    'camera': '相機',
    'calculator': '計算機',
    'laptop': '筆記型電腦',
    'clock': '時鐘',
    'donut': '甜甜圈',
    'wheel': '輪子',
    'ice_cream': '冰淇淋',
    'apple': '蘋果',
    'strawberry': '草莓'
};

export function toZh(en) {
    return zhMap[en] || en;
}
export function formatTimestamp(ts) {
    if (!ts) return '未知時間';

    try {
        let date;
        if (typeof ts === 'string') {
            // Remove microseconds if present (e.g. "2025-10-07T02:22:16.517424")
            const cleanedTs = ts.replace(/\.\d+$/, '');
            date = new Date(cleanedTs + 'Z'); // treat as UTC
        } else if (typeof ts === 'number') {
            date = new Date(ts > 1000000000000 ? ts : ts * 1000);
        } else {
            return '無效時間格式';
        }

        if (isNaN(date.getTime())) {
            console.error('Invalid date:', ts);
            return ts.toString();
        }

        // Convert to Asia/Taipei (GMT+8)
        const taipeiDate = new Date(date.getTime() + 8 * 60 * 60 * 1000);

        const year = taipeiDate.getUTCFullYear();
        const month = String(taipeiDate.getUTCMonth() + 1).padStart(2, '0');
        const day = String(taipeiDate.getUTCDate()).padStart(2, '0');
        const hour = String(taipeiDate.getUTCHours()).padStart(2, '0');
        const min = String(taipeiDate.getUTCMinutes()).padStart(2, '0');
        return `${year}-${month}-${day} ${hour}:${min}`;
    } catch (error) {
        console.error('Error formatting timestamp:', error);
        return '時間格式錯誤';
    }
}
export const API_BASE_URL = window.location.pathname.includes('quickdraw') 
  ? '/api/quickdraw' 
  : '/api';

export const getWebSocketURL = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/ws/quickdraw`;
};