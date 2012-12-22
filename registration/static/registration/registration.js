var reg_app = angular.module('registration',['registration.directives','ui']);

function MapCtrl($scope) {

    $scope.myMarkers = [];

    pnt = new google.maps.LatLng();
    $scope.mapOptions = {
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