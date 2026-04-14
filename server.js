const express = require('express');
const path = require('path');
const app = express();

// Serve static files from current directory
app.use(express.static(path.join(__dirname)));

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Zivio Demo running on port ${PORT}`);
});
