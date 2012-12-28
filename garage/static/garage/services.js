var mod = angular.module('garage.services',['tpResource']);

mod.factory('Profile', function($resource){
  return $resource('/garage/api/v1/profile/:userId', {}, {
    query: {method:'GET', params:{userId:""}, isArray:true}
  });
});