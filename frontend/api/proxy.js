export const config = {
  runtime: 'edge',
};

export default async function handler(request) {
  const url = new URL(request.url);
  const path = url.pathname.replace('/api/proxy', '');
  
  try {
    const backendUrl = `http://54.203.54.74:8000${path}${url.search}`;
    
    const response = await fetch(backendUrl, {
      method: request.method,
      headers: {
        'Content-Type': 'application/json',
      },
      body: request.method !== 'GET' ? await request.text() : undefined,
    });
    
    const data = await response.text();
    
    return new Response(data, {
      status: response.status,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
      },
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
    });
  }
}