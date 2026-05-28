const fs = require('fs');
const path = require('path');

const tabDir = path.join(__dirname, 'images/tab');

if (!fs.existsSync(tabDir)) {
  fs.mkdirSync(tabDir, { recursive: true });
}

const createPNG = (width, height, r, g, b, a = 255) => {
  const png = [];
  
  png.push(0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A);
  
  const ihdr = [
    (width >> 24) & 0xFF, (width >> 16) & 0xFF, (width >> 8) & 0xFF, width & 0xFF,
    (height >> 24) & 0xFF, (height >> 16) & 0xFF, (height >> 8) & 0xFF, height & 0xFF,
    8, 6, 0, 0, 0
  ];
  const ihdrCrc = crc32([0x49, 0x48, 0x44, 0x52, ...ihdr]);
  png.push(0, 0, 0, 13, 0x49, 0x48, 0x44, 0x52, ...ihdr, ...int32ToBytes(ihdrCrc));
  
  const rawData = [];
  for (let y = 0; y < height; y++) {
    rawData.push(0);
    for (let x = 0; x < width; x++) {
      rawData.push(r, g, b, a);
    }
  }
  
  const compressed = deflate(rawData);
  const idatCrc = crc32([0x49, 0x44, 0x41, 0x54, ...compressed]);
  const len = compressed.length;
  png.push((len >> 24) & 0xFF, (len >> 16) & 0xFF, (len >> 8) & 0xFF, len & 0xFF);
  png.push(0x49, 0x44, 0x41, 0x54, ...compressed, ...int32ToBytes(idatCrc));
  
  const iendCrc = crc32([0x49, 0x45, 0x4E, 0x44]);
  png.push(0, 0, 0, 0, 0x49, 0x45, 0x4E, 0x44, ...int32ToBytes(iendCrc));
  
  return Buffer.from(png);
};

const int32ToBytes = (val) => [
  (val >> 24) & 0xFF, (val >> 16) & 0xFF, (val >> 8) & 0xFF, val & 0xFF
];

const crc32Table = (() => {
  const table = [];
  for (let i = 0; i < 256; i++) {
    let c = i;
    for (let j = 0; j < 8; j++) {
      c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
    }
    table.push(c >>> 0);
  }
  return table;
})();

const crc32 = (data) => {
  let crc = 0xFFFFFFFF;
  for (const byte of data) {
    crc = crc32Table[(crc ^ byte) & 0xFF] ^ (crc >>> 8);
  }
  return (crc ^ 0xFFFFFFFF) >>> 0;
};

const deflate = (data) => {
  const result = [0x78, 0x01];
  const blockSize = 65535;
  
  for (let i = 0; i < data.length; i += blockSize) {
    const block = data.slice(i, Math.min(i + blockSize, data.length));
    const isLast = i + blockSize >= data.length;
    
    result.push(isLast ? 1 : 0);
    result.push(block.length & 0xFF, (block.length >> 8) & 0xFF);
    result.push((~block.length) & 0xFF, ((~block.length) >> 8) & 0xFF);
    result.push(...block);
  }
  
  let a = 1, b = 0;
  for (const byte of data) {
    a = (a + byte) % 65521;
    b = (b + a) % 65521;
  }
  const adler = ((b << 16) | a) >>> 0;
  result.push((adler >> 24) & 0xFF, (adler >> 16) & 0xFF, (adler >> 8) & 0xFF, adler & 0xFF);
  
  return result;
};

const icons = [
  { name: 'home', color: [138, 138, 138] },
  { name: 'home-active', color: [102, 126, 234] },
  { name: 'adoption', color: [138, 138, 138] },
  { name: 'adoption-active', color: [102, 126, 234] },
  { name: 'community', color: [138, 138, 138] },
  { name: 'community-active', color: [102, 126, 234] },
  { name: 'profile', color: [138, 138, 138] },
  { name: 'profile-active', color: [102, 126, 234] }
];

icons.forEach(({ name, color }) => {
  const png = createPNG(48, 48, ...color);
  fs.writeFileSync(path.join(tabDir, `${name}.png`), png);
  console.log(`Created ${name}.png`);
});

console.log('All tabBar icons created successfully!');