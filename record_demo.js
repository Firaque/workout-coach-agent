const puppeteer = require('puppeteer');
const { PuppeteerScreenRecorder } = require('puppeteer-screen-recorder');
const { execSync } = require('child_process');

(async () => {
    console.log("Launching browser...");
    const browser = await puppeteer.launch({
        executablePath: '/usr/bin/google-chrome',
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--window-size=1280,800',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu'
        ]
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 800 });

    page.on('console', msg => console.log('BROWSER LOG:', msg.text()));
    page.on('pageerror', err => console.log('BROWSER ERROR:', err.toString()));

    const recorder = new PuppeteerScreenRecorder(page, {
        followNewTab: false,
        fps: 30,
        ffmpeg_Path: '/usr/bin/ffmpeg',
        videoFrame: {
            width: 1280,
            height: 800,
        },
        aspectRatio: '16:9',
    });

    const outputVideo = 'demo_raw.mp4';
    await recorder.start(outputVideo);
    console.log("Started recording...");

    console.log("Navigating to Workout Coach Frontend...");
    await page.goto('https://workout-coach-agent-frontend-967591342130.us-east1.run.app', {
        waitUntil: 'networkidle2',
        timeout: 30000,
    });

    await new Promise(r => setTimeout(r, 2000));

    // Helper for typing like a human
    async function typeHuman(selector, text) {
        await page.focus(selector);
        for (let char of text) {
            await page.keyboard.sendCharacter(char);
            await new Promise(r => setTimeout(r, 35 + Math.random() * 25));
        }
    }

    // --- PROMPT 1: What chest exercises should I do today? ---
    console.log("Submitting Prompt 1: What chest exercises should I do today?");
    await typeHuman('#input', "What chest exercises should I do today?");
    await new Promise(r => setTimeout(r, 500));
    await page.click('button.send-btn');

    // Wait for agent message (.msg.agent)
    console.log("Waiting for agent response 1...");
    await page.waitForFunction(() => {
        const msgs = document.querySelectorAll('.msg.agent');
        return msgs.length >= 1;
    }, { timeout: 40000 });

    console.log("Agent response 1 received!");
    // Pause so viewer can comfortably read
    await new Promise(r => setTimeout(r, 6000));

    // --- PROMPT 2: Log 3 sets of 8 reps at 185 lbs for Barbell Bench Press and illustrate the exercise. ---
    console.log("Submitting Prompt 2: Richer tool call + database + image generation prompt...");
    await typeHuman('#input', "Log 3 sets of 8 reps at 185 lbs for Barbell Bench Press and illustrate the exercise.");
    await new Promise(r => setTimeout(r, 500));
    await page.click('button.send-btn');

    console.log("Waiting for agent response 2 (tool call + image generation)...");
    await page.waitForFunction(() => {
        const msgs = document.querySelectorAll('.msg.agent');
        return msgs.length >= 2;
    }, { timeout: 60000 });

    console.log("Agent response 2 received!");
    // Pause to show the logged workout & generated image
    await new Promise(r => setTimeout(r, 8000));

    console.log("Stopping recording...");
    await recorder.stop();
    await browser.close();
    console.log("Raw video recorded to demo_raw.mp4!");

    // Mix raw video with lofi background music using ffmpeg
    console.log("Mixing video with lofi background music...");
    const mixCmd = `ffmpeg -y -i demo_raw.mp4 -i lofi_bg_music.wav -c:v copy -c:a aac -b:a 192k -shortest workout_coach_demo.mp4`;
    execSync(mixCmd);
    console.log("Final demo video successfully generated at workout_coach_demo.mp4!");
})();
