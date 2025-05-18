const express = require('express');
const cors = require('cors');
const sqlite3 = require('sqlite3').verbose();
const bodyParser = require('body-parser');
const app = express();
const port = 3001;

// Middlewares
app.use(cors());
app.use(bodyParser.json());

// Base de datos
const db = new sqlite3.Database('./db/database.sqlite');

// Crear tabla ejemplo
db.serialize(() => {
  db.run(`CREATE TABLE IF NOT EXISTS reportes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descripcion TEXT NOT NULL,
    fecha TEXT NOT NULL
  )`);
});

// Rutas
app.get('/reportes', (req, res) => {
  db.all('SELECT * FROM reportes', [], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(rows);
  });
});

app.post('/reportes', (req, res) => {
  const { descripcion, fecha } = req.body;
  db.run(`INSERT INTO reportes (descripcion, fecha) VALUES (?, ?)`, [descripcion, fecha], function(err) {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ id: this.lastID });
  });
});

app.listen(port, () => {
  console.log(`Servidor backend corriendo en http://localhost:${port}`);
});
