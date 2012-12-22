//monkey patch to add centering to maps
angular.module('ui.directives').directive('uiMapCenter', [function(){
    return {
    priority: 0,
    restrict: 'A',
    //doesn't work as E for unknown reason
    link: function (scope, elm, attrs) {
        var coords = attrs.uiMapCenter.split(",");
        var center = new google.maps.LatLng(coords[0],coords[1]);
        scope.setCenter(center); 
    }
  };
}]);

/////////////////////////////////////////////////
// Paddock directives
/////////////////////////////////////////////////

var app = angular.module('registration.directives',[]);

app.directive('avatarPic', [function(){
    return {
    restrict: 'AC',
    link: function (scope, elm, attrs) {
        elm.popover( {
            trigger: 'hover',
            content: function(){
            var img_href = $(this).attr('href')
                return '<img src="'+img_href+'">'    
            },
            html:true
        });
    }
  };
}]);



