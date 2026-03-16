const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function parseSyllabus(formData: FormData) {
  const res = await fetch(`${API_BASE}/parse`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Failed to parse syllabus");
  return res.json();
}
