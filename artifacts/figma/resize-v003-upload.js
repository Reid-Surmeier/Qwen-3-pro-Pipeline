const assembly = await figma.getNodeByIdAsync("6:146");

if (!assembly || assembly.type !== "FRAME") {
  throw new Error("Expected uploaded assembly frame 6:146");
}

assembly.name = "golf-ui/club-assembly/v003 exact-preservation";
assembly.resize(600, 600 * 403 / 474);

return {
  mutatedNodeIds: [assembly.id],
  nodes: [
    {
      id: assembly.id,
      name: assembly.name,
      width: assembly.width,
      height: assembly.height,
    },
  ],
};
