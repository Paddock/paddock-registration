var reg_app = angular.module('registration',['paddock.directives','ui']);

function MapCtrl($scope) {

    pnt = new google.maps.LatLng();
    $scope.myMap = null;
    $scope.mapOptions = {
      zoom: 11,
      mapTypeId: google.maps.MapTypeId.ROADMAP
    }; 

    $scope.setCenter = function(pnt) {
      console.log($scope.myMap);
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