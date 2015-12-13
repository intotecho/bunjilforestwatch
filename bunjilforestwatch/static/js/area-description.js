function init_area_descriptions(url) {
	"use strict";
	 
    // Update Area Description properties
    $('.update-area-btn').click(function(e) {
        var elem = $(e.target);
        elem.html('Saving...');
    	var p =  elem.parent().parent();
    	
    	var id = p.attr('id');
        var gp =  p.parent();
        var text = (id === 'area-wiki-form') ?  gp.find('input').val() : gp.find('textarea').val();
        /*
        if(id === 'area-wiki-form') {
        	text = gp.find('input').val();
        }
        else {
        	text = gp.find('textarea').val();
        }
        */  
        var patch_ops =  [];
        
        switch (id) {
        	case 'area_descr_what':
	        	patch_ops.push( { "op": "replace", "path": "/properties/area_description/description", "value": text, "id": id });
	        	break;

        	case 'area_descr_why':
	        	patch_ops.push( { "op": "replace", "path": "/properties/area_description/description_why", "value": text, "id": id });
	        	break;

        	case 'area_descr_how':
	        	patch_ops.push( { "op": "replace", "path": "/properties/area_description/description_how", "value": text, "id": id });
	        	break;

        	case 'area_descr_who':
	        	patch_ops.push( { "op": "replace", "path": "/properties/area_description/description_who", "value": text, "id": id });
	        	break;
	
        	case 'area_descr_threats':
	        	patch_ops.push( { "op": "replace", "path": "/properties/area_description/threats", "value": text, "id": id });
	        	break;
    
        	case 'area-wiki-form':
	        	patch_ops.push( { "op": "replace", "path": "/properties/area_description/wiki", "value": text, "id": id });
	        	break;
	        	
	        default:
	            console.log("update-area-btn Error: id:" + id  + ', div:' + gp + ', patch:' + patch_ops);
	        	break;
        }
        
        //console.log("update-area-btn id:" + id  + ', div:' + gp + ', patch:' + patch_ops[0]);
        var request = patch_area(patch_ops, url);  //patch_area(); //ajax call
        
        request.done(function (data) {
        	if(typeof data !== 'undefined') {
        		console.log ('patch_area() result: ' + data.status + ', ' 
        						+ data.updates.length + ' updates: ' + data.updates[0].result);
        	}
    		gp.find('.dirty-flag').hide(); //move to ajax response.
    	    gp.find('.update-area-btn').attr('disabled', true).html('Saved');
        });
        
        request.fail(function (xhr, textStatus, error) {
			  console.log ('patch_area() - request failed:', xhr.status, ' error: ', error);
	    	  gp.find('.update-area-btn').attr('color', 'red').html('Error');
        })
    });
    
    $('#area-description-panel textarea').on('change', function(e) {
    	var p =  $(e.target).parent().parent().parent();
        p.find('.dirty-flag').show();
        p.find('.update-area-btn').attr('disabled', false).html('Save');
    });

} //end-of-init-area-description
