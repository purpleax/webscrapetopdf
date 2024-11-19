const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');
const { URL } = require('url');

// Set to keep track of visited URLs
const visitedUrls = new Set();

async function debugMessage(message) {
  console.log(`[${new Date().toISOString()}] ${message}`);
}

async function getInternalLinks(page, url, baseDomain) {
  const links = await page.evaluate(() =>
    Array.from(document.querySelectorAll('a[href]'), a => a.href)
  );

  // Filter internal links
  return links.filter(link => {
    try {
      const linkUrl = new URL(link);
      return linkUrl.hostname === baseDomain && !visitedUrls.has(linkUrl.href);
    } catch (err) {
      return false;
    }
  });
}

async function savePageAsPDF(page, url, outputPath) {
  try {
    await page.goto(url, { waitUntil: 'load', timeout: 30000 });
    await page.pdf({
      path: outputPath,
      format: 'A4',
      printBackground: true,
    });
    await debugMessage(`Saved ${url} to ${outputPath}`);
    return outputPath;
  } catch (err) {
    await debugMessage(`Error saving ${url} to PDF: ${err}`);
    return null;
  }
}

async function downloadPDF(url, outputPath) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to download PDF from ${url}`);
  }
  const buffer = await response.buffer();
  fs.writeFileSync(outputPath, buffer);
  await debugMessage(`Downloaded PDF from ${url} to ${outputPath}`);
  return outputPath;
}

async function crawlAndSave(page, url, baseDomain, outputDir, depth, pdfOnly, downloadPDFs) {
  if (depth === 0 || visitedUrls.has(url)) {
    return [];
  }

  visitedUrls.add(url);
  const pdfFiles = [];
  const isPDF = url.endsWith('.pdf');

  if (isPDF) {
    const pdfPath = path.join(outputDir, path.basename(url));
    if (pdfOnly || downloadPDFs) {
      await downloadPDF(url, pdfPath);
      pdfFiles.push(pdfPath);
    }
  } else if (!pdfOnly) {
    const outputPath = path.join(outputDir, `${url.replace(/[:/]+/g, '_')}.pdf`);
    const pdfPath = await savePageAsPDF(page, url, outputPath);
    if (pdfPath) {
      pdfFiles.push(pdfPath);
    }

    const internalLinks = await getInternalLinks(page, url, baseDomain);
    for (const link of internalLinks) {
      const childPdfs = await crawlAndSave(page, link, baseDomain, outputDir, depth - 1, pdfOnly, downloadPDFs);
      pdfFiles.push(...childPdfs);
    }
  }

  return pdfFiles;
}

async function main() {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    console.error('Usage: node script.js <url> --depth=<depth> --pdf-only --download-pdfs');
    process.exit(1);
  }

  const targetUrl = args[0];
  const depth = parseInt(args.find(arg => arg.startsWith('--depth='))?.split('=')[1]) || 2;
  const pdfOnly = args.includes('--pdf-only');
  const downloadPDFs = args.includes('--download-pdfs');

  const baseDomain = new URL(targetUrl).hostname;
  const outputDir = baseDomain;
  fs.mkdirSync(outputDir, { recursive: true });

  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();

  await page.setUserAgent(
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'
  );

  const pdfFiles = await crawlAndSave(page, targetUrl, baseDomain, outputDir, depth, pdfOnly, downloadPDFs);

  if (args.includes('--single-pdf') && pdfFiles.length > 0) {
    const PDFMerger = require('pdf-merger-js');
    const merger = new PDFMerger();

    for (const pdf of pdfFiles) {
      merger.add(pdf);
    }

    const combinedOutput = path.join(outputDir, 'combined_document.pdf');
    await merger.save(combinedOutput);
    await debugMessage(`Combined PDF saved as ${combinedOutput}`);
  }

  await browser.close();
  await debugMessage('Crawling completed.');
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
