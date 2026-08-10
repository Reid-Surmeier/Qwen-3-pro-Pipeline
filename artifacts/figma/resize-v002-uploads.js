const variant = await figma.getNodeByIdAsync("4:146");
const contactSheet = await figma.getNodeByIdAsync("4:147");

if (!variant || variant.type !== "FRAME") {
  throw new Error("Expected uploaded variant frame 4:146");
}
if (!contactSheet || contactSheet.type !== "FRAME") {
  throw new Error("Expected uploaded contact-sheet frame 4:147");
}

variant.name = "golf-ui/club-preview/v002-2";
variant.resize(600, 600 * 806 / 948);

contactSheet.name = "golf-ui/club-preview/v002 contact sheet";
contactSheet.x = variant.x + variant.width + 80;
contactSheet.y = variant.y;
contactSheet.resize(600, 600 * 978 / 988);

return {
  mutatedNodeIds: [variant.id, contactSheet.id],
  nodes: [
    { id: variant.id, name: variant.name, width: variant.width, height: variant.height },
    {
      id: contactSheet.id,
      name: contactSheet.name,
      width: contactSheet.width,
      height: contactSheet.height,
    },
  ],
};
