const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const svgPath = 'd:\\Code\\brands_icons\\merx-ipc-horizon-dome.svg';
const brandDir = 'd:\\Code\\merx-horizon-ipc-camera-connector\\custom_components\\merx_horizon\\brand';

if (!fs.existsSync(brandDir)) {
    fs.mkdirSync(brandDir, { recursive: true });
}

async function convert() {
    try {
        // Create icon.png (typically 256x256 or 512x512)
        await sharp(svgPath)
            .resize(512, 512, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
            .png()
            .toFile(path.join(brandDir, 'icon.png'));
        console.log('Created icon.png');

        // Create logo.png (can be wider or just the same, let's use the same for now)
        await sharp(svgPath)
            .resize(512, 512, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
            .png()
            .toFile(path.join(brandDir, 'logo.png'));
        console.log('Created logo.png');
        
        // Also create @2x versions
        await sharp(svgPath)
            .resize(1024, 1024, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
            .png()
            .toFile(path.join(brandDir, 'icon@2x.png'));
        console.log('Created icon@2x.png');

        await sharp(svgPath)
            .resize(1024, 1024, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
            .png()
            .toFile(path.join(brandDir, 'logo@2x.png'));
        console.log('Created logo@2x.png');

    } catch (err) {
        console.error('Error converting SVG:', err);
    }
}

convert();
