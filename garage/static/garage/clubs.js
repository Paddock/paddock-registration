var app = angular.module('clubs',['ngCookies', 'ui', 'tpResource',
    'paddock.directives', 'garage.services']);

app.controller('club_admin', function club_admin($scope,$cookies,Profile,Club){
    $scope.profile = Profile.get({userId:USER_ID},function(){
        //console.log($scope.profile);
    });
    $scope.club = Club.get({clubId:CLUB_ID},function(){
        //console.log($scope.club);
    });

    $scope.show_edit_event = false;
    
    $scope.edit_event = function(event) {
        $scope.edit_event_target = angular.copy(event);
        $scope.event_modal_title = 'Edit ' + event.name;
        $scope.edit_event_target.date = new Date(event.date);
        console.log($scope.edit_event_target);
        $scope.show_event_modal = true;
    };

    $scope.new_event = function(season) {
        $scope.edit_event_target = {season:season}
        $scope.event_modal_title = 'New Event'
        $scope.show_event_modal = true;
    };

    $scope.cancel_save_event = function(){
        $scope.show_event_modal = false;
    };

    $scope.save_event = function(){
        //do some save crap
        $scope.show_event_modal = false;
    };

});

app.config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('', {templateUrl: STATIC_URL+'/garage/clubs.html',
        controller: 'club_admin'});
    $routeProvider.otherwise({redirectTo: ''});
}]);
