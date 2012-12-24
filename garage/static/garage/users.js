var app = angular.module('users',['ui','tpResource'])

app.controller('user_admin', function user(){
    
});

app.config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('', {templateUrl: STATIC_URL+'/garage/users.html', controller: 'user_admin'});
    $routeProvider.otherwise({redirectTo: ''});
}]);
