# ArkPedra — design notes

## Reading

- Audience: owners and commercial teams at marmorarias; end customers use the simulator.
- Product: a five-stage quote simulator that turns stone, dimensions and finish choices into a WhatsApp-ready request.
- First-screen belief: ArkPedra lets a customer build a useful quote request without waiting for the first manual reply.
- Proof: the real, working simulator and its generated WhatsApp message.
- Primary action: "Simular orçamento".

## Subject inventory

- Ark + Pedra: a digital structure made from a physical material.
- Full stone slabs and the mineral veins that make every piece different.
- Measuring tape, cut line and centimetres.
- The worktable where a slab becomes a countertop.
- Stone selection by colour, grain and finish.
- Sink cutout, backsplash, edge profile and installation.
- A quote assembled line by line.
- A finished kitchen as the promise; a marked slab as the process.
- WhatsApp as the handoff from digital estimate to human service.
- Five decisions, kept in order, without losing context.

## Argument

1. The customer can start a stone quote now. → working simulator visible immediately after the opening.
2. Stone choice should feel material, not abstract. → photographic stone selector with four real-looking surfaces.
3. Five decisions become one useful request. → live quote summary and WhatsApp preview.
4. The tool reduces back-and-forth without replacing final validation. → concise process copy and explicit estimate disclaimer.
5. The next step is to try it. → closing action returns to the simulator.

## Direction

- Dealt direction: The name as a monument, seed 476134076.
- Dealt app direction: Framed sheet, seed 1193092704.
- Palette adjustment: the dealt soot-and-lime palette was mapped to soapstone, calcite and mineral green because acid lime on black is a generic AI-site tell and does not match natural stone.
- Type: Boska, one editorial family, with a serif fallback.
- Layout: tight 16–32px margins; the word ArkPedra is the architectural event; the simulator is a pale working sheet inside a dark stone frame.
- Alignment: primarily left aligned, with a reused one-third text axis.
- Principles: material before decoration; scale before cards; photographs do the colour work; the simulator is the proof.

## Idea

On this page, ArkPedra's slab, vein and cut line become the architecture that holds the product interface.

Competitor test: another marmoraria could use stone photography, but not the ArkPedra name split into Ark/Pedra as the structural frame around a live five-step digital quote. The combination belongs to this product.

Live thing: the real five-step quote simulator, with photographic stone selection, validation, live summary and a generated WhatsApp request.

## Copy deck

- Hero title: ArkPedra.
- Support: Seu cliente escolhe a pedra, informa as medidas e envia uma estimativa organizada para o WhatsApp da marmoraria.
- Primary action: Simular orçamento.
- Simulator heading: Comece pela pedra.
- Material section: A matéria vem primeiro.
- Process section: Do corte à conversa.
- Benefits section: Menos vai e volta.
- Closing: Um pedido que já chega claro.

## Verification note

The source lint finished with 0 FAIL and 2 expected warnings for 1px boundaries inside the real `data-ui` simulator interface. A screenshot critique was not scored: `inspect.mjs` could not find Chrome/Edge/Chromium, and the available in-app browser rejected the local `file://` preview. No visual score is claimed without rendered screenshots. Final pixel review at 1440, 768 and 390 px remains the one environmental limitation of this run.

