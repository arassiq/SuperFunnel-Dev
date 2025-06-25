fetch("https://workjustflows-567041770002.herokuapp.com/runTaskGen", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",      //sending json
    "Authorization": "123e4567-e89b-12d3-a456-426614174000"              // this becomes userAuthHeader in FastAPI
  },
  body: JSON.stringify({
    usrTaskInput: "Buy groceries and clean the garage"
  })
})
  .then(response => response.json())
  .then(data => {
    console.log("Structured task:", data);
  })
  .catch(error => {
    console.error("Error calling backend:", error);
  });