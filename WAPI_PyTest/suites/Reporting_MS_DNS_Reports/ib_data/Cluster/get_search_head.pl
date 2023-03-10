 use strict;
 use Infoblox;
#Retriving Search Head HW ID to perform system related activity. 
 my $host_ip = $ARGV[0];
 my $search_head_file = $ARGV[1];
 my $hw_info = $ARGV[2];
 my $session = Infoblox::Session->new( master   => $host_ip, username => "admin", password => "infoblox" );
 my @result = $session->get( object=>"Infoblox::Grid::Member::Reporting",);
 my $member;
 foreach my $ref (@result)
 {
     my %node_info = %$ref;
     if ( $node_info{"role"} eq "SEARCH_HEAD_INDEXER" )
     {
       $member = $node_info{"name"};
       $member =~ m/(\d+)-(\d+)-(\d+)-(\d+)/g;
       my $ip="$1.$2.$3.$4";
       my $hw = `grep $ip $hw_info | cut -d : -f 2`;
       open(NODE,"> $search_head_file");
       print NODE $hw;
       close(NODE);

       open(NODE_IP,"> $search_head_file.ip");
       print NODE_IP $ip;
       close(NODE_IP);
     }
 }
