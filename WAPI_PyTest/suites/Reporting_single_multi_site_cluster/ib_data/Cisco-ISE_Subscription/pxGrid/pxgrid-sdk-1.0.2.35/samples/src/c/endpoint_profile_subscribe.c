#include <stdlib.h>
#include <unistd.h>
#include <memory.h>
#include "pxgrid.h"
#include "helper.h"

#include <openssl/ssl.h>
#define UNUSED(x) (void)(x)

int _pem_key_password_cb(char *buf, int size, int rwflag, void *userdata) {
    UNUSED(rwflag);
    helper_config *hconfig = userdata;
    strncpy(buf, hconfig->client_cert_key_password, size);
    buf[size - 1] = '\0';
    return (int)strlen(buf);
}

static void _user_ssl_ctx_cb( pxgrid_connection *connection, void *_ssl_ctx, void *user_data ) {
   
    helper_config *hconfig = user_data;
    SSL_CTX *ssl_ctx = _ssl_ctx;
    printf("_user_ssl_ctx_cb calling \n");
    SSL_CTX_set_default_passwd_cb(ssl_ctx, _pem_key_password_cb);
    SSL_CTX_set_default_passwd_cb_userdata(ssl_ctx, hconfig);  
    SSL_CTX_use_certificate_chain_file(ssl_ctx, hconfig->client_cert_chain_filename);
    SSL_CTX_use_PrivateKey_file(ssl_ctx, hconfig->client_cert_key_filename, SSL_FILETYPE_PEM);
    SSL_CTX_load_verify_locations(ssl_ctx, hconfig->server_cert_chain_filename, NULL);    
    SSL_CTX_set_verify(ssl_ctx, SSL_VERIFY_PEER, NULL);   
}
static void _on_disconnected(pxgrid_connection *connection, PXGRID_STATUS status, void *user_data) {
    UNUSED(connection);
    UNUSED(user_data);
	printf("disconnected!!! status=%s\n", pxgrid_status_get_message(status));
}

static void _on_connected(pxgrid_connection *connection, void *user_data) {
   UNUSED(connection);
   UNUSED(user_data);
   printf("wow connected!!!\n");
 }
 
static void message_callback(jw_dom_node *node, void *arg) {
    UNUSED(arg);
	jw_dom_node *type_node = jw_dom_get_first_element(node ,"changeType");
	jw_dom_node *profile_node = jw_dom_get_first_element(node ,"endpointProfile");
	
    if (profile_node){
		ise_endpoint_profile *profile;
        ise_endpoint_profile_create(&profile, profile_node);
        ise_endpoint_profile_print(profile);
		if(type_node)  ise_print_changetype( type_node );		
	    ise_endpoint_profile_destroy(profile);
    }	
}

int main(int argc, char **argv) 
{
	PXGRID_STATUS status;
    helper_config *hconfig = NULL;
    pxgrid_config *conn_config = NULL;
    pxgrid_connection *connection = NULL;
    helper_config_create(&hconfig, argc, argv); 
    if(!hconfig) 
	{
	    printf("Unable to create hconfig object\n");
			exit(EXIT_FAILURE); 
	}  
    helper_pxgrid_config_create(hconfig , &conn_config);
    pxgrid_connection_create( &connection );
     
    // Set connection configuration data
    pxgrid_connection_set_config(connection , conn_config);

    // Set Call back
    pxgrid_connection_set_disconnect_cb(connection, _on_disconnected);	
	pxgrid_connection_set_connect_cb(connection, _on_connected);
    
    pxgrid_connection_set_ssl_ctx_cb(connection, (pxgrid_connection_ssl_ctx_cb)_user_ssl_ctx_cb);
    pxgrid_connection_set_ssl_ctx_cb_user_data(connection, (helper_config *)hconfig);

    // make a connection to given host
    pxgrid_connection_connect(connection);
    
    
	pxgrid_capability *capability = NULL;
	pxgrid_capability_create(&capability);
    
    char namespacebuf[] = "http://www.cisco.com/pxgrid/identity";
    char namebuf[] = "EndpointProfileMetaDataCapability";
    
	pxgrid_capability_set_namespace(capability, namespacebuf);
	pxgrid_capability_set_name(capability, namebuf);
    
	char notf_buf[] = 	"http://www.cisco.com/pxgrid/identity";
    char notf_hdl_buf[] ="endpointProfileChangedNotification";
	pxgrid_capability_subscribe(capability, connection);
	pxgrid_connection_register_notification_handler(connection, notf_buf, notf_hdl_buf, message_callback, NULL);
	
    sleep(600);
	pxgrid_connection_disconnect(connection);
	printf("*** disconnected\n");

	pxgrid_capability_destroy(capability);
	pxgrid_connection_destroy(connection);
	pxgrid_config_destroy(conn_config);
    helper_config_destroy(hconfig);
       
	return 0;
}
