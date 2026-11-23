import { cp, access } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = fileURLToPath(new URL("..", import.meta.url));
const standalone = path.join(root, ".next", "standalone");
await access(path.join(standalone, "server.js"));
await cp(
  path.join(root, ".next", "static"),
  path.join(standalone, ".next", "static"),
  { recursive: true },
);
await cp(path.join(root, "public"), path.join(standalone, "public"), {
  recursive: true,
});
process.env.HOSTNAME = "127.0.0.1";
process.env.PORT ??= "3000";
await import(pathToFileURL(path.join(standalone, "server.js")).href);
