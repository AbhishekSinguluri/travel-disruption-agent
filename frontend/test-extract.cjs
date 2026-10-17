const puppeteer = require('puppeteer-core');

async function run() {
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    headless: true
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1200, height: 800 });
  await page.goto('http://localhost:5173');
  await new Promise(r => setTimeout(r, 2000));
  
  const colors = await page.evaluate(async () => {
     const canvas = document.createElement('canvas');
     canvas.width = 1200;
     canvas.height = 800;
     const ctx = canvas.getContext('2d');
     // We can't render DOM to canvas easily without html2canvas, but we can just use the video element directly.
     const video = document.querySelector('video');
     if (!video) return 'No video';
     
     // Draw the video to canvas
     ctx.drawImage(video, 0, 0, 1200, 800);
     const pixel = ctx.getImageData(10, 10, 1, 1).data;
     
     return `rgb(${pixel[0]}, ${pixel[1]}, ${pixel[2]})`;
  });
  
  console.log("Video raw background color:", colors);
  await browser.close();
}

run();
