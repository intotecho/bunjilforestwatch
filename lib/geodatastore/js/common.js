if(typeof console == "undefined"){
 var console = {log:function(){}}
}

if (typeof geodatastore == "undefined") {
  var geodatastore = {};
}

geodatastore.createMapWithSidebar = function(wrapper_div) {
  var table = document.createElement('table');
  table.style.width = '100%';
  if (window.innerHeight) {
    var height = window.innerHeight - 150;
  } else {
    var height = document.documentElement.offsetHeight - 150;
  }
  height = height + "px";

  var tbody = document.createElement('tbody');
  table.appendChild(tbody);

  var tr = document.createElement('tr');

  var map_td = document.createElement('td');
  map_td.height = height;
  var map_div = document.createElement('div');
  map_div.style.width = '100%';
  map_div.style.height = '100%';
  map_div.style.border = '1px solid #eeeeee';
  map_td.appendChild(map_div);

  var sidebar_td = document.createElement('td');
  sidebar_td.width = '29%';
  sidebar_td.height = height;
  var sidebar_div = document.createElement('div');
  sidebar_div.id = 'sidebar';
  sidebar_div.style.overflow = 'scroll';
  sidebar_div.style.border = '1px solid #eeeeee';
  sidebar_div.style.height = height;
  sidebar_td.appendChild(sidebar_div);

  tr.appendChild(map_td);
  tr.appendChild(sidebar_td);
  tbody.appendChild(tr);

  wrapper_div.appendChild(table);

  return {map_div: map_div, sidebar_div: sidebar_div};
}

