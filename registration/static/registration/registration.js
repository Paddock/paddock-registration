var reg_app = angular.module('registration',['paddock.directives','ui']);

function MapCtrl($scope) {

    pnt = new google.maps.LatLng();
    $scope.myMap = null;
    $scope.mapOptions = {
      zoom: 11,
      mapTypeId: google.maps.MapTypeId.ROADMAP
    }; 

    $scope.setCenter = function(sc, pnt) {
      var marker = new google.maps.Marker({
        map: sc.myMap,
        position: pnt
        });
      google.maps.event.addListener(marker, 'click',function() {
        sc.myInfoWindow.open($scope.myMap, marker);
      });
      sc.myMap.setCenter(pnt);
    };
}