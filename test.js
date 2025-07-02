const res = await fetch("https://workjustflows-567041770002.herokuapp.com/runTaskGen", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "userAuthHeader": "123e4567-e89b-12d3-a456-426614174000"
  },
  body: JSON.stringify("Create a roadmap for the Q3 launch")
});

const text = await res.text();
try {
  const result = JSON.parse(text);
  console.log("Parsed JSON:", result);
} catch (e) {
  console.error("Failed to parse response:", text);
}