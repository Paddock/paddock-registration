var reg_app = angular.module('registration',['paddock.directives','ui']);

function MapCtrl($scope) {

    pnt = new google.maps.LatLng(map_center_coords[0],map_center_coords[1]);
    $scope.mapOptions = {
      center: pnt,
      zoom: 11,
      mapTypeId: google.maps.MapTypeId.ROADMAP
    }; 

    // when the map gets set, add a marker 
    $scope.$watch('myMap',function(oldMap,newMap){
      var marker = new google.maps.Marker({
        map: newMap,
        position: pnt
        });
      google.maps.event.addListener(marker, 'click',function() {
        $scope.myInfoWindow.open(newMap, marker);
      });
    });

}{}