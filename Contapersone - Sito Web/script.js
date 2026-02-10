const e = React.createElement;

function Home() {
  return e(
    "div",
    { className: "home" },
    e(
      "header",
      null,
      e("h1", null, "Contapersone")
    )
  );
}

function App() {
  return e(Home);
}

// Render
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(e(App));
