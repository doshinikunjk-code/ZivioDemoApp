export const EL_VOICE_ID = 'mActWQg9kibLro6Z2ouY';

export const MENU_ITEMS = {
  'butter chicken': 'Butter Chicken Cones',
  'bc cone': 'Butter Chicken Cones',
  'lamb chop': 'Shahi Lamb Chops',
  'lamb': 'Shahi Lamb Chops',
  'dal makhani': 'Dal Makhani',
  'palak paneer': 'Palak Paneer',
  'paneer': 'Palak Paneer',
  'raj kachori': 'Raj Kachori',
  'kachori': 'Raj Kachori',
  'chicken tikka': 'Chicken Tikka',
  'tikka': 'Chicken Tikka',
  'biryani': 'Chicken Biryani',
  'paneer taco': 'Paneer Hardshell Tacos',
  'taco': 'Paneer Hardshell Tacos',
  'seekh kebab': 'Seekh Kebab',
  'kebab': 'Seekh Kebab',
  'garlic naan': 'Garlic Naan',
  'naan': 'Garlic Naan',
  'butter naan': 'Butter Naan',
  'mango lassi': 'Mango Lassi',
  'lassi': 'Mango Lassi',
  'masala chai': 'Masala Chai',
  'chai': 'Masala Chai',
  'gulab jamun': 'Gulab Jamun',
  'kulfi': 'Kulfi Falooda',
  '\u0a2c\u0a1f\u0a30 \u0a1a\u0a3f\u0a15\u0a28': 'Butter Chicken Cones',
  '\u0a28\u0a3e\u0a28': 'Garlic Naan',
  '\u0a32\u0a71\u0a38\u0a40': 'Mango Lassi',
  '\u0a32\u0a48\u0a02\u0a2c': 'Shahi Lamb Chops',
  '\u092c\u091f\u0930 \u091a\u093f\u0915\u0928': 'Butter Chicken Cones',
  '\u0928\u093e\u0928': 'Garlic Naan',
  '\u0932\u0938\u094d\u0938\u0940': 'Mango Lassi',
  '\u0932\u0948\u0902\u092c': 'Shahi Lamb Chops',
};

export const DONE_WORDS = [
  'confirm', 'pakka', 'done', 'theek', 'bas', "that's all", 'that is all',
  'ho gaya', 'pucca', 'finalize', 'complete', 'buss', 'hogaya'
];

export const ADD_ORDER_WORDS = [
  'add to my order', 'just ordered', 'called earlier', 'add more',
  'hor paao', 'aur dena', 'same again', 'wahi order', 'phir se'
];

export const ORDER_COMPLETE_PHRASES = [
  'see you at desi road', 'ready in', 'milte hain', 'taiyar',
  'mildte haan', '20 min', 'tiar', 'pickup'
];

export const OFFLINE_REPLIES = [
  { m: ['butter chicken', 'bc cone'], r: "Butter Chicken Cones — note kar liya ji! Kuch aur?" },
  { m: ['lamb chop', 'lamb'], r: "Shahi Lamb Chops — done ji! Aur kuch?" },
  { m: ['naan', 'garlic naan'], r: "Garlic Naan — added! Kuch aur chahiye?" },
  { m: ['lassi', 'mango lassi'], r: "Mango Lassi — haan ji, noted!" },
  { m: ['menu', 'kya hai', 'what do you have'], r: "Ji, humare paas hai — Butter Chicken Cones, Lamb Chops, Dal Makhani, Garlic Naan, Mango Lassi — kya mangwana hai?" },
  { m: ['confirm', 'pakka', 'done', 'theek', 'bas'], r: "Order pakka ho gaya ji! 20 minute mein ready. Desi Road mein milte hain!" },
  { m: ['halal'], r: "Haan ji, sab kuch halal hai bilkul!" },
  { m: ['price', 'how much', 'kitna'], r: "Butter Chicken Cones $16.99 | Lamb Chops $29.99 | Naan $3.99 | Lassi $5.99" },
  { m: ['hour', 'open', 'timing'], r: "Mon-Sat 11am-11pm, Sun 12pm-10pm ji" },
  { m: ['parking'], r: "Haan ji, parking ki koi dikkat nahi!" },
  { m: ['hi', 'hello', 'hey', 'sat sri', 'namaste'], r: "Sat Sri Akal ji! Desi Road mein aapka swagat hai. Kya order karna chahenge?" },
];

export function getOfflineReply(text) {
  const l = (text || '').toLowerCase();
  for (const o of OFFLINE_REPLIES) {
    if (o.m.some(m => l.includes(m))) return o.r;
  }
  return "Sat Sri Akal ji! Desi Road mein swagat hai. Kya mangwana hai aaj?";
}

export function detectOrderItems(text, currentItems) {
  const l = text.toLowerCase();
  const found = [];
  for (const [key, val] of Object.entries(MENU_ITEMS)) {
    if (l.includes(key) && !currentItems.includes(val) && !found.includes(val)) {
      found.push(val);
    }
  }
  return found;
}

export function stripPrices(text) {
  if (!text) return text;
  if (/^[\w\s]+ ?[—\-–] ?\$[\d.]+\.?$/.test(text.trim())) return text;
  return text
    .replace(/\$[\d]+\.?[\d]*/g, '')
    .replace(/\bSubtotal:?.*$/gim, '')
    .replace(/\bTotal:?.*$/gim, '')
    .replace(/  +/g, ' ')
    .trim();
}
