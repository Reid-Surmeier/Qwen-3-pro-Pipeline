const uploaded = await figma.getNodeByIdAsync('125:257');
const source = await figma.getNodeByIdAsync('110:989');

if (!uploaded || uploaded.removed) {
  throw new Error('Uploaded Palantir threat-report badge node 125:257 was not found');
}
if (!source || source.removed) {
  throw new Error('Energy Star source node 110:989 was not found');
}

uploaded.name = 'sticker/palantir-threat-report-included/energy-star-cursive-qwen/v001';
uploaded.resize(320, 320);
uploaded.x = source.x;
uploaded.y = source.y + source.height + 80;

return {
  createdNodeIds: [],
  mutatedNodeIds: [uploaded.id],
  sourceNodeId: source.id,
  sourceReplaced: false,
  connectorCreated: false,
  placed: {
    id: uploaded.id,
    name: uploaded.name,
    x: uploaded.x,
    y: uploaded.y,
    width: uploaded.width,
    height: uploaded.height,
  },
};
