var reg_app = angular.module('registration',['paddock.directives','ui']);

function MapCtrl($scope) {

    pnt = new google.maps.LatLng();
    $scope.mapOptions = {
      center: new google.maps.LatLng(map_center_coords[0],map_center_coords[1]),
      zoom: 11,
      mapTypeId: google.maps.MapTypeId.ROADMAP
    }; 

    $scope.setCenter = function(pnt) {
      var marker = new google.maps.Marker({
        map: $scope.myMap,
        position: pnt
        });
      google.maps.event.addListener(marker, 'click',function() {
        $scope.myInfoWindow.open($scope.myMap, marker);
      });
      $scope.myMap.setCenter(pnt);
    };
}