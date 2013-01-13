var app = angular.module('clubs',['ngCookies', 'ui', 'tpResource',
    'paddock.directives', 'garage.services']);

app.controller('club_admin', function club_admin($scope,$cookies,$http,Profile,Club){
    $scope.csrf = $cookies.csrftoken;

    $scope.profile = Profile.get({userId:USER_ID},function(){
        //console.log($scope.profile);
    });
    $scope.club = Club.get({clubId:CLUB_ID},function(){
        //console.log($scope.club);
        $scope.location_map = {};
        angular.forEach($scope.club.locations,function(l,index){
            $scope.location_map[l.id] = index;
        });
        $scope.new_event_season = $scope.club.seasons[0];

        angular.forEach($scope.club.seasons,function(season,index){
            $scope.$watch('club.seasons['+index+'].drop_lowest_events',function(newVal,oldVal){
                //todo: autosave here
                //console.log(newVal);
            });
        });

    });

    $scope.show_edit_event = false;
    $scope.default_reg_close = true;

    $scope.new_season = function(){
        var year = $scope.club.seasons[0].year + 1;
        $scope.club.seasons.unshift({year:year})
        $scope.new_event_season = $scope.club.seasons[0];
    };

    $scope.upload_results = function(event){

    };

    $scope.delete_event = function(season,event) {
        if(confirm("You're about to delete "+event.name+". You will lose all the event data, including results!" )){
            var i = season.events.indexOf(event);
            season.events.splice(i,1);
        }
    };

    $scope.build_event_msg = function(event) {
        $scope.event_msg_target = event;
        $scope.show_event_msg_modal = true;
    }

    $scope.send_event_msg = function(event) {
        $http({method:'POST',url:'/garage/event/'+event.id+'/email_drivers',
            data:$.param({'subject':$scope.event_msg_subject,
                'body':$scope.event_msg_body}),
            headers:{'X-CSRFToken':$scope.csrf},
        });
        $scope.show_event_msg_modal = false;
    }
    
    $scope.edit_event = function(event) {
        $scope.edit_event_target = angular.copy(event);
        $scope.event_modal_title = 'Edit ' + event.name;
        $scope.edit_event_target.date = new Date(event.date);
        $scope.edit_event_target.reg_close = new Date(event.reg_close);
        $scope.edit_event_location = event.location.id
        $scope.show_event_modal = true;
    };

    $scope.new_event = function(season) {
        $scope.edit_event_target = {season:season}
        $scope.event_modal_title = 'New Event'
        $scope.default_reg_close = true;
        $scope.show_event_modal = true;
    };

    $scope.cancel_save_event = function(){
        $scope.show_event_modal = false;
    };

    $scope.save_event = function(){
        if($scope.default_reg_close){
            var d = $scope.edit_event_target.date;

            // get sets it to the first hour of the day
            var midnight = new Date(d.getFullYear(),
                d.getMonth(), d.getDate());
            
            $scope.edit_event_target.reg_close = midnight;
        }
        var i = $scope.location_map[$scope.edit_event_location]
        $scope.edit_event_target.location = $scope.club.locations[i];
        //$scope.show_event_modal = false;

        //don't need to manually update the data, because angular seems 
        //to re-load it at the end of the save from the modal
    };

});

app.config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('', {templateUrl: STATIC_URL+'/garage/clubs.html',
        controller: 'club_admin'});
    $routeProvider.otherwise({redirectTo: ''});
}]);
