(function exposePricing(root, factory) {
  const pricing = factory();

  if (typeof module === 'object' && module.exports) module.exports = pricing;
  if (root) root.ArkPedraPricing = pricing;
}(typeof globalThis !== 'undefined' ? globalThis : this, function createPricing() {
  function calculateQuote(options) {
    const {
      length,
      depth,
      quantity,
      stonePrice,
      sink,
      backsplash,
      finish,
      installation,
    } = options;

    const area = (length * depth / 10000) * quantity;
    const material = area * stonePrice;
    const front = (length / 100) * (backsplash / 100) * stonePrice * quantity;
    const edge = (length / 100) * finish * quantity;
    const extras = sink + front + edge + installation;

    return {
      area,
      material,
      front,
      edge,
      extras,
      total: material + extras,
    };
  }

  function buildWhatsAppMessage(details) {
    const sink = details.sinkPosition ? `${details.sink} — ${details.sinkPosition}` : details.sink;
    return `Olá! Fiz uma simulação na ArkPedra.\n\nPedra: ${details.stone}\nMedidas: ${details.length} × ${details.depth} cm (${details.quantity} peça${details.quantity > 1 ? 's' : ''})\nCuba: ${sink}\nFrontão: ${details.backsplash}\nAcabamento: ${details.finish}\nInstalação: ${details.installation}\nEstimativa: ${details.formattedTotal}\n\nGostaria de confirmar o orçamento.`;
  }

  return Object.freeze({ calculateQuote, buildWhatsAppMessage });
}));
