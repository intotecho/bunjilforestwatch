const categories = ['Fire', 'Deforestation', 'Agriculture', 'Road', 'Unsure'];

const categoryImages = {
  'Fire': require('../images/fire.png'),
  'Deforestation': require('../images/deforestation.png'),
  'Agriculture': require('../images/agriculture.png'),
  'Road': require('../images/road.png'),
  'Unsure': require('../images/unsure.png')
};

const regionPreference = {
  'congo': require('../images/congo.png'),
  'peru': require('../images/peru.jpeg'),
  'indonesia': require('../images/indonesia.png')
};

export {
  regionPreference,
  categories,
  categoryImages
};