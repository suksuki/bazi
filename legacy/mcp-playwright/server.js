const { Server } = require("@modelcontextprotocol/sdk/server/index.js");
const { StdioServerTransport } = require("@modelcontextprotocol/sdk/server/stdio.js");
const { CallToolRequestSchema, ListToolsRequestSchema } = require("@modelcontextprotocol/sdk/types.js");
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const server = new Server(
    {
        name: "playwright-custom",
        version: "0.1.0",
    },
    {
        capabilities: {
            tools: {},
        },
    }
);

let browser;
let context;

server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
        tools: [
            {
                name: "browser_navigate",
                description: "Navigate to a URL",
                inputSchema: {
                    type: "object",
                    properties: {
                        url: { type: "string" },
                    },
                    required: ["url"],
                },
            },
            {
                name: "browser_click",
                description: "Click an element by selector",
                inputSchema: {
                    type: "object",
                    properties: {
                        selector: { type: "string" },
                    },
                    required: ["selector"],
                },
            },
            {
                name: "browser_eval",
                description: "Run arbitrary JavaScript on the page",
                inputSchema: {
                    type: "object",
                    properties: {
                        script: { type: "string" },
                    },
                    required: ["script"],
                },
            },
            {
                name: "browser_screenshot",
                description: "Take a screenshot of the current page",
                inputSchema: {
                    type: "object",
                    properties: {
                        name: { type: "string" },
                    },
                    required: ["name"],
                },
            },
        ],
    };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
    if (!browser) {
        browser = await chromium.launch({ headless: false });
        context = await browser.newContext();
    }
    const page = context.pages()[0] || (await context.newPage());

    switch (request.params.name) {
        case "browser_navigate": {
            const url = request.params.arguments.url;
            await page.goto(url, { waitUntil: 'networkidle' });
            return {
                content: [{ type: "text", text: `Navigated to ${url}` }],
            };
        }
        case "browser_click": {
            const selector = request.params.arguments.selector;
            await page.click(selector);
            return {
                content: [{ type: "text", text: `Clicked ${selector}` }],
            };
        }
        case "browser_eval": {
            const script = request.params.arguments.script;
            const result = await page.evaluate(script);
            return {
                content: [{ type: "text", text: `Result: ${JSON.stringify(result)}` }],
            };
        }
        case "browser_screenshot": {
            const name = request.params.arguments.name;
            const screenshotDir = "/home/jin/bazi_predict/screenshots";
            if (!fs.existsSync(screenshotDir)) {
                fs.mkdirSync(screenshotDir, { recursive: true });
            }
            const screenshotPath = path.join(screenshotDir, `${name}.png`);
            await page.screenshot({ path: screenshotPath });
            return {
                content: [{ type: "text", text: `Screenshot saved to ${screenshotPath}` }],
            };
        }
        default:
            throw new Error("Unknown tool");
    }
});

async function main() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
}

main().catch((err) => {
    fs.appendFileSync("/home/jin/bazi_predict/mcp-playwright/error.log", err.stack + "\n");
    process.exit(1);
});
