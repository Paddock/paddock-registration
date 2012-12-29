var app = angular.module('users',['ui','tpResource','garage.services'])

app.controller('user_admin', function user($scope,Profile,Car){
    $scope.profile = Profile.get({userId:USER_ID});

    $scope.save_user = function(){
        //console.log('Saving: ',$scope.user.first_name)
        Profile.save($scope.profile)
    }

    $scope.del_car = function(car){
        //console.log(car);
        var i = $scope.profile.cars.indexOf(car);
        var car_id = $scope.profile.cars[i].id;
        //console.log(i)
        Car.remove({'carId':car_id},function(){
            $scope.profile.cars.splice(i,1)
        });
        
    }
});

app.config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('', {templateUrl: STATIC_URL+'/garage/users.html', controller: 'user_admin'});
    $routeProvider.otherwise({redirectTo: ''});
}]);
