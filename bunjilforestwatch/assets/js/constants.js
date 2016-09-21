const categories = ['Fire', 'Deforestation', 'Agriculture', 'Road', 'Unsure'];

const categoryImages = {
  'Fire': require('../images/fire.png'),
  'Deforestation': require('../images/deforestation.png'),
  'Agriculture': require('../images/agriculture.png'),
  'Road': require('../images/road.png'),
  'Unsure': require('../images/unsure.png')
};

const regionPreference = {
  'borneo': require('../images/borneo.jpeg'),
  'peru': require('../images/peru.jpeg')
};

export {
  regionPreference,
  categories,
  categoryImages
};