
const e = React.createElement;

// Header
function Header() {
  return e(
    "header",
    null,
    e("h1", null, "Il mio sito con React"),
    e("p", null, "Senza JSX, senza build 😎")
  );
}

// Contatore
function Counter() {
  const [count, setCount] = React.useState(0);

  return e(
    "div",
    null,
    e("h2", null, "Contatore"),
    e("p", null, "Valore: " + count),
    e(
      "button",
      { onClick: () => setCount(count + 1) },
      "Aumenta"
    )
  );
}

// Lista
function Lista() {
  const [items, setItems] = React.useState(["ALALALALA"]);

  function aggiungiElemento() {
    setItems([...items, "Elemento " + (items.length + 1)]);
  }

  return e(
    "div",
    null,
    e("h2", null, "Lista dinamica"),
    e(
      "ul",
      null,
      items.map((item, index) =>
        e("li", { key: index }, item)
      )
    ),
    e(
      "button",
      { onClick: aggiungiElemento },
      "Aggiungi"
    )
  );
}

// Footer
function Footer() {
  return e(
    "footer",
    null,
    e("p", null, "© 2026 - React CDN")
  );
}

// App principale
function App() {
  return e(
    "div",
    null,
    e(Header),
    e(
      "main",
      null,
      e(Counter),
      e("hr"),
      e(Lista)
    ),
    e(Footer)
  );
}

// Render
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(e(App));

