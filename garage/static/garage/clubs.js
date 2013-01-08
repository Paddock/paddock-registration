var app = angular.module('clubs',['ngCookies','ui','tpResource','paddock.directives','garage.services'])

app.controller('club_admin', function club($scope,$cookies,Profile,Club){
    $scope.club = Club.query({clubId: 'noraascc'}, function(){
        console.log($scope.club);
    })
});

app.config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('', {templateUrl: STATIC_URL+'/garage/clubs.html', controller: 'club_admin'});
    $routeProvider.otherwise({redirectTo: ''});
}]);