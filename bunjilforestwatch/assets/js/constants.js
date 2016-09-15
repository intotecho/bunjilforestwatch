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

// Remove when tested
const regionPreferenceTest = {
  'borneo': require('../images/borneo.jpeg'),
  'borneo1': require('../images/borneo.jpeg'),
  'borneo2': require('../images/borneo.jpeg'),
  'borneo3': require('../images/borneo.jpeg'),
  'borneo4': require('../images/borneo.jpeg'),
  'borneo5': require('../images/borneo.jpeg'),
  'borneo6': require('../images/borneo.jpeg'),
  'borneo7': require('../images/borneo.jpeg'),
  'borneo8': require('../images/borneo.jpeg'),
  'borneo9': require('../images/borneo.jpeg'),
  'peru': require('../images/peru.jpeg'),
  'peru1': require('../images/peru.jpeg'),
  'peru2': require('../images/peru.jpeg'),
  'peru3': require('../images/peru.jpeg'),
  'peru4': require('../images/peru.jpeg'),
  'peru5': require('../images/peru.jpeg'),
  'peru6': require('../images/peru.jpeg'),
  'peru7': require('../images/peru.jpeg'),
  'peru8': require('../images/peru.jpeg'),
  'peru9': require('../images/peru.jpeg'),
};

export {
  regionPreference,
  regionPreferenceTest,
  categories,
  categoryImages
};