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

var app = angular.module('paddock.directives',[]);

app.directive('avatarPopover', [function(){
    return {
    restrict: 'E',
    link: function (scope, elm, attrs) {
        if (attrs.ngRef){
            var target = scope.$eval(attrs.ngRef);
        }else {
            var target = attrs.href;
        }

        if (attrs.ngDataTitle){
            var title = scope.$eval(attrs.ngDataTitle);
        }else{
            var title = attrs.dataTitle;
        }
        elm.html('<i class="icon-picture avatar_pic" data-title="'+title+'"></i>')
        elm.popover( {
            trigger: 'hover',
            content: function(){
                return '<img src="'+target+'">'    
            },
            html:true
        });
    }
  };
}]);



