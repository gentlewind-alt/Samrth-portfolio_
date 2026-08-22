// Shared "slaps landed" counter for the static portfolio on Vercel.
//
//   GET  /api/slaps  -> { count }
//   POST /api/slaps  -> { count }   (atomic increment)
//
// Backed by a Redis-compatible KV store over its REST API, called with plain
// fetch so this needs no dependencies -- the Vercel project has a blank build
// command, so nothing would install them.
//
// Provision a KV store in the Vercel dashboard (Storage -> Upstash Redis) and
// it injects the env vars below automatically. Until then this returns 503 and
// the page falls back to its per-browser localStorage count.

const KEY = 'chiyo:slaps';

const REST_URL = process.env.KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL;
const REST_TOKEN = process.env.KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN;

async function redis(command) {
  const res = await fetch(`${REST_URL}/${command}/${KEY}`, {
    headers: { Authorization: `Bearer ${REST_TOKEN}` },
    cache: 'no-store'
  });
  if (!res.ok) throw new Error(`KV ${command} failed: ${res.status}`);
  const body = await res.json();
  return parseInt(body.result, 10) || 0;
}

module.exports = async (req, res) => {
  res.setHeader('Cache-Control', 'no-store');

  if (!REST_URL || !REST_TOKEN) {
    res.status(503).json({ error: 'KV store not configured' });
    return;
  }

  try {
    if (req.method === 'POST') {
      res.status(200).json({ count: await redis('incr') });
    } else if (req.method === 'GET') {
      res.status(200).json({ count: await redis('get') });
    } else {
      res.setHeader('Allow', 'GET, POST');
      res.status(405).json({ error: 'Method not allowed' });
    }
  } catch (err) {
    res.status(502).json({ error: String(err.message || err) });
  }
};
