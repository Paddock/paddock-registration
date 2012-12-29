var app = angular.module('users',['ui','tpResource','garage.services'])

app.controller('user_admin', function user($scope,Profile){
    $scope.profile = Profile.get({userId:USER_ID});

    $scope.save_user = function(){
        //console.log('Saving: ',$scope.user.first_name)
        Profile.save($scope.profile)
    }
});

app.config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('', {templateUrl: STATIC_URL+'/garage/users.html', controller: 'user_admin'});
    $routeProvider.otherwise({redirectTo: ''});
}]);
