const e = React.createElement;

function Home() {
  return e(
    "div",
    { className: "home" },
    e(
      "header",
      null,
      e("h1", null, "Contapersone"),
      e("h2", {id: "stt"}, "siete sotto sorveglianza!")
    )
  );
}

function App() {
  return e(Home);
}

// Render
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(e(App));


