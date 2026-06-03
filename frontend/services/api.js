const API_URL = import.meta.env.VITE_API_URL;

export async function sendQuery(query) {
    const response = await fetch(`${API_URL}/query`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ query }),
    });
    return await response.json();
}