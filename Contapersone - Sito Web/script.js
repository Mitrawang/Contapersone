const e = React.createElement;
const { useState, useEffect } = React;

function Home() {
  const [visible, setVisible] = useState(false);
  const [entrate, setEntrate] = useState(0);
  const [uscite, setUscite] = useState(0);
  const [presenti, setPresenti] = useState(0);

  useEffect(() => {
    setVisible(true);
    
    // Funzione per ottenere i contatori dal backend
    const fetchData = async () => {
      try {
        // Qui puoi collegare il tuo endpoint PHP o Python
        const response = await fetch('api_count.php');
        const data = await response.json();
        
        setEntrate(data.entrate);
        setUscite(data.uscite);
        setPresenti(data.presenti);
      } catch (error) {
        console.error('Errore nel recupero dati:', error);
        
        // Dati di esempio per test (rimuovi in produzione)
        setEntrate(Math.floor(Math.random() * 20));
        setUscite(Math.floor(Math.random() * 15));
        setPresenti(Math.floor(Math.random() * 10));
      }
    };

    // Chiamata iniziale
    fetchData();

    // Aggiornamento ogni secondo
    const interval = setInterval(fetchData, 1000);

    // Cleanup
    return () => clearInterval(interval);
  }, []);

  return e(
    "div",
    { className: "home" },
    e(
      "header",
      { className: visible ? "fade-in visible" : "fade-in" },
      e("h1", null, "Contapersone"),
      e("h2", { id: "stt" }, "siete sotto sorveglianza!"),
      
      // Container per i tre contatori
      e("div", { className: "contatori-container" },
        
        // Contatore presenti
        e("div", { className: "contatore-box presenti-box" },
          e("span", { className: "contatore-label" }, "PRESENTI"),
          e("div", { className: "contatore valore-blu" }, presenti)
        ),
        
        // Contatore entrate
        e("div", { className: "contatore-box" },
          e("span", { className: "contatore-label" }, "ENTRATE"),
          e("div", { className: "contatore valore-verde" }, entrate)
        ),
        
        // Contatore uscite
        e("div", { className: "contatore-box" },
          e("span", { className: "contatore-label" }, "USCITE"),
          e("div", { className: "contatore valore-rosso" }, uscite)
        )
      )
    )
  );
}

function App() {
  return e(Home);
}

// Render
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(e(App));
