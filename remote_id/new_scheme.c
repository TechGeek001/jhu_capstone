/*
 * Copyright (C) 2021, Soren Friis
 *
 * SPDX-License-Identifier: Apache-2.0
 *
 * Open Drone ID Linux transmitter example.
 *
 * Maintainer: Soren Friis
 * friissoren2@gmail.com
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <pthread.h>
#include <semaphore.h>
#include <signal.h>
#include <errno.h>
#include <sys/resource.h>
#include "transmitter-linux/ap_interface.h"
#include "transmitter-linux/bluetooth.h"
#include "transmitter-linux/wifi_beacon.h"
#include "transmitter-linux/gpsmod.h"
#include "transmitter-linux/core-c/libopendroneid/opendroneid.h"

#include "openssl/sha.h"
#include <openssl/ecdsa.h>
#include <openssl/ec.h>
#include <openssl/obj_mac.h>

sem_t semaphore;
pthread_t id, gps_thread;

#define MINIMUM(a,b) (((a)<(b))?(a):(b))

#define BASIC_ID_POS_ZERO 0
#define BASIC_ID_POS_ONE 1

static struct config_data config = { 0 };
static bool kill_program = false;

static struct fixsource_t source;
static struct gps_data_t gpsdata;

struct gps_loop_args {
    struct gps_data_t *gpsdata;
    struct ODID_UAS_Data *uasData;
    int exit_status;
};

static void hash_basic_id(struct ODID_BasicID_data *BasicID, SHA256_CTX *sha256) {
    SHA256_Update(sha256, BasicID->UASID, sizeof(BasicID->UASID));
}

static void hash_location(struct ODID_Location_data *location, SHA256_CTX *sha256) {
    int Direction = (int)location->Direction;
    int SpeedHorizontal = (int)location->SpeedHorizontal;
    int SpeedVertical = (int)location->SpeedVertical;
    int Latitude = (int)location->Latitude;
    int Longitude = (int)location->Longitude;
    int AltitudeBaro = (int)location->AltitudeBaro;
    int AltitudeGeo = (int)location->AltitudeGeo;
    int Height = (int)location->Height;
    int Timestamp = (int)location->TimeStamp;
    SHA256_Update(sha256, &Direction, sizeof(int));
    SHA256_Update(sha256, &SpeedHorizontal, sizeof(int));
    SHA256_Update(sha256, &SpeedVertical, sizeof(int));
    SHA256_Update(sha256, &Latitude, sizeof(int));
    SHA256_Update(sha256, &Longitude, sizeof(int));
    SHA256_Update(sha256, &AltitudeBaro, sizeof(int));
    SHA256_Update(sha256, &AltitudeGeo, sizeof(int));
    SHA256_Update(sha256, &Height, sizeof(int));
    SHA256_Update(sha256, &Timestamp, sizeof(int));
}

static void hash_system(struct ODID_System_data *system, SHA256_CTX *sha256) {
    int OperatorLatitude = (int)system->OperatorLatitude;
    int OperatorLongitude = (int)system->OperatorLongitude;
    int AreaCeiling = (int)system->AreaCeiling;
    int AreaFloor = (int)system->AreaFloor;
    int OperatorAltitudeGeo = (int)system->OperatorAltitudeGeo;
    SHA256_Update(sha256, &OperatorLatitude, sizeof(int));
    SHA256_Update(sha256, &OperatorLongitude, sizeof(int));
    SHA256_Update(sha256, &OperatorAltitudeGeo, sizeof(int));
    SHA256_Update(sha256, &(system->Timestamp), sizeof(uint32_t));
}

static void sign_data(struct ODID_UAS_Data *uasData, EC_KEY *ec_key) {
    unsigned char hash[SHA256_DIGEST_LENGTH];
    SHA256_CTX sha256;
    SHA256_Init(&sha256);
    hash_basic_id(&uasData->BasicID[0], &sha256);
    hash_basic_id(&uasData->BasicID[1], &sha256);
    hash_location(&uasData->Location, &sha256);
    SHA256_Update(&sha256, uasData->SelfID.Desc, sizeof(uasData->SelfID.Desc));
    hash_system(&uasData->System, &sha256);
    SHA256_Update(&sha256, uasData->OperatorID.OperatorId, sizeof(uasData->OperatorID.OperatorId));
    SHA256_Final(hash, &sha256);
    uint32_t signature_len = ECDSA_size(ec_key);
    uint8_t* signature = (uint8_t *) OPENSSL_malloc(signature_len);
    ECDSA_sign(0, (const uint8_t *)hash, SHA256_DIGEST_LENGTH, signature, &signature_len, ec_key);
    printf("Message SHA256: ");for (uint32_t i = 0; i < SHA256_DIGEST_LENGTH; i++) printf("%02x", hash   [i]); printf("\n");
    printf("Signature     : "); for(uint32_t i = 0; i < signature_len       ; i++) printf("%02x", signature[i]); printf("\n");

    bool verification = ECDSA_verify(0, hash, SHA256_DIGEST_LENGTH, signature, signature_len, ec_key);
    if (verification == 1)
        printf("Verification successful\n");
    else
        printf("Verification NOT successful\n");
    EC_KEY_free(ec_key);
    printf("signature_len: %d\n",signature_len);
    int pages = signature_len/24 + 1;
    uasData->Auth[0].Length = signature_len;
    memcpy(uasData->Auth[0].AuthData, signature, 17);
    printf("Auth Page 0     : "); for(uint32_t z = 0; z < 17; z++) printf("%02x", uasData->Auth[0].AuthData[z]); printf("\n");
    
    for (int i=0; i < pages; i++) {
        uasData->Auth[0].LastPageIndex = i+1;
        uasData->Auth[i].AuthType = ODID_AUTH_UAS_ID_SIGNATURE;uasData->Auth[i].DataPage = i;
        memcpy(uasData->Auth[i].AuthData, signature+i*sizeof(uasData->Auth[i].AuthData)+17, 
        MINIMUM(signature_len-sizeof(uasData->Auth[i].AuthData)*i-17, sizeof(uasData->Auth[i].AuthData)));
        printf("Auth Page %d     : ", i+1); for(uint32_t z = 0; z < MINIMUM(signature_len-sizeof(uasData->Auth[i].AuthData)*i-17, sizeof(uasData->Auth[i].AuthData)); z++) printf("%02x", uasData->Auth[i].AuthData[z]); printf("\n");
    }
    OPENSSL_free(signature);
}   

static void fill_example_data(struct ODID_UAS_Data *uasData) {
    uasData->BasicID[BASIC_ID_POS_ZERO].UAType = ODID_UATYPE_HELICOPTER_OR_MULTIROTOR;
    uasData->BasicID[BASIC_ID_POS_ZERO].IDType = ODID_IDTYPE_SERIAL_NUMBER;
    char uas_id[] = "112624150A90E3AE1EC0";
    strncpy(uasData->BasicID[BASIC_ID_POS_ZERO].UASID, uas_id,
            MINIMUM(sizeof(uas_id), sizeof(uasData->BasicID[BASIC_ID_POS_ZERO].UASID)));

    uasData->BasicID[BASIC_ID_POS_ONE].UAType = ODID_UATYPE_HELICOPTER_OR_MULTIROTOR;
    uasData->BasicID[BASIC_ID_POS_ONE].IDType = ODID_IDTYPE_SPECIFIC_SESSION_ID;
    char uas_caa_id[] = "FD3454B778E565C24B70";
    strncpy(uasData->BasicID[BASIC_ID_POS_ONE].UASID, uas_caa_id,
            MINIMUM(sizeof(uas_caa_id), sizeof(uasData->BasicID[BASIC_ID_POS_ONE].UASID)));

    uasData->Auth[0].AuthType = ODID_AUTH_UAS_ID_SIGNATURE;
    uasData->Auth[0].DataPage = 0;
    uasData->Auth[0].LastPageIndex = 2;
    uasData->Auth[0].Length = 63;
    uasData->Auth[0].Timestamp = 28000000;
    char auth0_data[] = "12345678901234567";
    memcpy(uasData->Auth[0].AuthData, auth0_data,
           MINIMUM(sizeof(auth0_data), sizeof(uasData->Auth[0].AuthData)));

    uasData->Auth[1].AuthType = ODID_AUTH_UAS_ID_SIGNATURE;
    uasData->Auth[1].DataPage = 1;
    char auth1_data[] = "12345678901234567890123";
    memcpy(uasData->Auth[1].AuthData, auth1_data,
           MINIMUM(sizeof(auth1_data), sizeof(uasData->Auth[1].AuthData)));

    uasData->Auth[2].AuthType = ODID_AUTH_UAS_ID_SIGNATURE;
    uasData->Auth[2].DataPage = 2;
    char auth2_data[] = "12345678901234567890123";
    memcpy(uasData->Auth[2].AuthData, auth2_data,
           MINIMUM(sizeof(auth2_data), sizeof(uasData->Auth[2].AuthData)));

    uasData->SelfID.DescType = ODID_DESC_TYPE_TEXT;
    char description[] = "This is a test of a spoofed drone id";
    strncpy(uasData->SelfID.Desc, description,
            MINIMUM(sizeof(description), sizeof(uasData->SelfID.Desc)));

    uasData->System.OperatorLocationType = ODID_OPERATOR_LOCATION_TYPE_TAKEOFF;
    uasData->System.ClassificationType = ODID_CLASSIFICATION_TYPE_EU;
    uasData->System.OperatorLatitude = uasData->Location.Latitude + 0.001;
    uasData->System.OperatorLongitude = uasData->Location.Longitude - 0.001;
    uasData->System.AreaCount = 1;
    uasData->System.AreaRadius = 0;
    uasData->System.AreaCeiling = 0;
    uasData->System.AreaFloor = 0;
    uasData->System.CategoryEU = ODID_CATEGORY_EU_OPEN;
    uasData->System.ClassEU = ODID_CLASS_EU_CLASS_1;
    uasData->System.OperatorAltitudeGeo = 20.5f;
    uasData->System.Timestamp = 28056789;

    uasData->OperatorID.OperatorIdType = ODID_OPERATOR_ID;
    char operatorId[] = "Not Real";
    strncpy(uasData->OperatorID.OperatorId, operatorId,
            MINIMUM(sizeof(operatorId), sizeof(uasData->OperatorID.OperatorId)));
}

static void fill_example_gps_data(struct ODID_UAS_Data *uasData) {
    uasData->Location.Status = ODID_STATUS_AIRBORNE;
    uasData->Location.Direction = 361.f;
    uasData->Location.SpeedHorizontal = 0.0f;
    uasData->Location.SpeedVertical = 0.35f;
    uasData->Location.Latitude = 51.4791;
    uasData->Location.Longitude = -0.0013;
    uasData->Location.AltitudeBaro = 100;
    uasData->Location.AltitudeGeo = 110;
    uasData->Location.HeightType = ODID_HEIGHT_REF_OVER_GROUND;
    uasData->Location.Height = 80;
    uasData->Location.HorizAccuracy = createEnumHorizontalAccuracy(5.5f);
    uasData->Location.VertAccuracy = createEnumVerticalAccuracy(9.5f);
    uasData->Location.BaroAccuracy = createEnumVerticalAccuracy(0.5f);
    uasData->Location.SpeedAccuracy = createEnumSpeedAccuracy(0.5f);
    uasData->Location.TSAccuracy = createEnumTimestampAccuracy(0.1f);
    uasData->Location.TimeStamp = 360.52f;
}

static void cleanup(int exit_code) {
    if (config.use_btl || config.use_bt4 || config.use_bt5)
        close_bluetooth(&config);

    if (config.use_beacon) {
        send_quit();

        int *ptr;
        pthread_join(id, (void **) &ptr);
        printf("Return value from ap_interface_init: %i\n", *ptr);

        sem_destroy(&semaphore);
    }

    if(config.use_gps) {
        int *ptr;
        pthread_join(gps_thread, (void **) &ptr);
        printf("Return value from gps_loop: %d\n", *ptr);

        gps_close(&gpsdata);
    }

    exit(exit_code);
}

static void sig_handler(int signo) {
    if (signo == SIGINT || signo == SIGSTOP || signo == SIGKILL || signo == SIGTERM) {
        kill_program = true;
    }
}

static void send_message(union ODID_Message_encoded *encoded, struct config_data *config, uint8_t msg_counter) {
    if (config->use_btl)
        send_bluetooth_message(encoded, msg_counter, config);
    if (config->use_bt4 || config->use_bt5)
        send_bluetooth_message_extended_api(encoded, msg_counter, config);
    if (config->use_beacon)
        send_beacon_message(encoded, msg_counter);
    usleep(100000);
}

// When using the WiFi Beacon transport method, the standards require that all messages are wrapped
// in a message pack and sent together. This single message send function is only for testing purposes.
static void send_single_messages(struct ODID_UAS_Data *uasData, struct config_data *config) {
    union ODID_Message_encoded encoded;
    memset(&encoded, 0, sizeof(union ODID_Message_encoded));

    for (int i = 0; i < 1; i++) {
        if (encodeBasicIDMessage((ODID_BasicID_encoded *) &encoded, &uasData->BasicID[BASIC_ID_POS_ZERO]) != ODID_SUCCESS)
            printf("Error: Failed to encode Basic ID\n");
        send_message(&encoded, config, config->msg_counters[ODID_MSG_COUNTER_BASIC_ID]++);
        if (encodeBasicIDMessage((ODID_BasicID_encoded *) &encoded, &uasData->BasicID[BASIC_ID_POS_ONE]) != ODID_SUCCESS)
            printf("Error: Failed to encode Basic ID\n");
        send_message(&encoded, config, config->msg_counters[ODID_MSG_COUNTER_BASIC_ID]++);

        if (encodeLocationMessage((ODID_Location_encoded *) &encoded, &uasData->Location) != ODID_SUCCESS)
            printf("Error: Failed to encode Location\n");
        send_message(&encoded, config, config->msg_counters[ODID_MSG_COUNTER_LOCATION]++);

        if (encodeAuthMessage((ODID_Auth_encoded *) &encoded, &uasData->Auth[0]) != ODID_SUCCESS)
            printf("Error: Failed to encode Auth 0\n");
        send_message(&encoded, config, config->msg_counters[ODID_MSG_COUNTER_AUTH]++);
        if (encodeAuthMessage((ODID_Auth_encoded *) &encoded, &uasData->Auth[1]) != ODID_SUCCESS)
            printf("Error: Failed to encode Auth 1\n");
        send_message(&encoded, config, config->msg_counters[ODID_MSG_COUNTER_AUTH]++);
        if (encodeAuthMessage((ODID_Auth_encoded *) &encoded, &uasData->Auth[2]) != ODID_SUCCESS)
            printf("Error: Failed to encode Auth 2\n");
        send_message(&encoded, config, config->msg_counters[ODID_MSG_COUNTER_AUTH]++);

        if (encodeSelfIDMessage((ODID_SelfID_encoded *) &encoded, &uasData->SelfID) != ODID_SUCCESS)
            printf("Error: Failed to encode Self ID\n");
        send_message(&encoded, config, config->msg_counters[ODID_MSG_COUNTER_SELF_ID]++);

        if (encodeSystemMessage((ODID_System_encoded *) &encoded, &uasData->System) != ODID_SUCCESS)
            printf("Error: Failed to encode System\n");
        send_message(&encoded, config, config->msg_counters[ODID_MSG_COUNTER_SYSTEM]++);

        if (encodeOperatorIDMessage((ODID_OperatorID_encoded *) &encoded, &uasData->OperatorID) != ODID_SUCCESS)
            printf("Error: Failed to encode Operator ID\n");
        send_message(&encoded, config, config->msg_counters[ODID_MSG_COUNTER_OPERATOR_ID]++);
    }
}

static void create_message_pack(struct ODID_UAS_Data *uasData, struct ODID_MessagePack_encoded *pack_enc) {
    union ODID_Message_encoded encoded = { 0 };
    ODID_MessagePack_data pack_data = { 0 };
    pack_data.SingleMessageSize = ODID_MESSAGE_SIZE;
    pack_data.MsgPackSize = 9;
    if (encodeBasicIDMessage((ODID_BasicID_encoded *) &encoded, &uasData->BasicID[BASIC_ID_POS_ZERO]) != ODID_SUCCESS)
        printf("Error: Failed to encode Basic ID\n");
    memcpy(&pack_data.Messages[0], &encoded, ODID_MESSAGE_SIZE);
    if (encodeBasicIDMessage((ODID_BasicID_encoded *) &encoded, &uasData->BasicID[BASIC_ID_POS_ONE]) != ODID_SUCCESS)
        printf("Error: Failed to encode Basic ID\n");
    memcpy(&pack_data.Messages[1], &encoded, ODID_MESSAGE_SIZE);
    if (encodeLocationMessage((ODID_Location_encoded *) &encoded, &uasData->Location) != ODID_SUCCESS)
        printf("Error: Failed to encode Location\n");
    memcpy(&pack_data.Messages[2], &encoded, ODID_MESSAGE_SIZE);
    if (encodeAuthMessage((ODID_Auth_encoded *) &encoded, &uasData->Auth[0]) != ODID_SUCCESS)
        printf("Error: Failed to encode Auth 0\n");
    memcpy(&pack_data.Messages[3], &encoded, ODID_MESSAGE_SIZE);
    if (encodeAuthMessage((ODID_Auth_encoded *) &encoded, &uasData->Auth[1]) != ODID_SUCCESS)
        printf("Error: Failed to encode Auth 1\n");
    memcpy(&pack_data.Messages[4], &encoded, ODID_MESSAGE_SIZE);
    if (encodeAuthMessage((ODID_Auth_encoded *) &encoded, &uasData->Auth[2]) != ODID_SUCCESS)
        printf("Error: Failed to encode Auth 2\n");
    memcpy(&pack_data.Messages[5], &encoded, ODID_MESSAGE_SIZE);
    if (encodeSelfIDMessage((ODID_SelfID_encoded *) &encoded, &uasData->SelfID) != ODID_SUCCESS)
        printf("Error: Failed to encode Self ID\n");
    memcpy(&pack_data.Messages[6], &encoded, ODID_MESSAGE_SIZE);
    if (encodeSystemMessage((ODID_System_encoded *) &encoded, &uasData->System) != ODID_SUCCESS)
        printf("Error: Failed to encode System\n");
    memcpy(&pack_data.Messages[7], &encoded, ODID_MESSAGE_SIZE);
    if (encodeOperatorIDMessage((ODID_OperatorID_encoded *) &encoded, &uasData->OperatorID) != ODID_SUCCESS)
        printf("Error: Failed to encode Operator ID\n");
    memcpy(&pack_data.Messages[8], &encoded, ODID_MESSAGE_SIZE);
    if (encodeMessagePack(pack_enc, &pack_data) != ODID_SUCCESS)
        printf("Error: Failed to encode message pack_data\n");
}

static void send_packs(struct ODID_UAS_Data *uasData, struct config_data *config) {
    struct ODID_MessagePack_encoded pack_enc = { 0 };
    create_message_pack(uasData, &pack_enc);

    for (int i = 0; i < 10; i++) {
        if (config->use_beacon)
            send_beacon_message_pack(&pack_enc, config->msg_counters[ODID_MSG_COUNTER_PACKED]++);
        if (config->use_bt5)
            send_bluetooth_message_pack(&pack_enc, config->msg_counters[ODID_MSG_COUNTER_PACKED]++, config);
        sleep(4);
    }
}

void print_help() {
    printf("Program for transmitting static drone ID data on Wi-Fi Beacon or Bluetooth.\n");
    printf("Must be run with sudo rights in order to work.\n");
    printf("Options: b Enable Wi-Fi Beacon transmission\n");
    printf("         l Enable Bluetooth 4 Legacy Advertising transmission\n");
    printf("           using the non-Extended Advertising HCI API commands\n");
    printf("         4 Enable Bluetooth 4 Legacy Advertising transmission\n");
    printf("           using the Extended Advertising HCI API commands\n");
    printf("         5 Enable Bluetooth 5 Long Range + Extended Advertising transmission\n");
    printf("         p Use message packs instead of single messages\n");
    printf("         g Use gpsd to dynamically update location messages after each loop of messages\n");
    printf("E.g. sudo ./transmit b p\n\n");
    printf("Wi-Fi Beacon transmit only works when running\n");
    printf("\"sudo hostapd/hostapd/hostapd beacon.conf\" in a separate shell.\n");
    printf("Disconnect from all Wi-Fi networks before starting Wi-Fi Beacon transmission.\n\n");
    printf("If terminated abnormally, Beacon and Bluetooth broadcasts can remain on.\n");
    printf(" - To stop Beacon broadcast, stop the hostapd instance.\n");
    printf("   It can be difficult to stop the transmit instance.\n");
    printf("   After stopping hostapd, use \"sudo pkill transmit\".\n");
    printf(" - To stop Bluetooth, use \"sudo btmgmt power off\" and then\n");
    printf("   \"sudo btmgmt power on\".\n");
}

static void parse_command_line(int argc, char *argv[], struct config_data *config) {
    if (argc == 1) {
        print_help();
        exit(EXIT_SUCCESS);
    }

    for (int i = 1; i < argc; i++) {
        switch (*argv[i]) {
            case 'b':
                config->use_beacon = true;
                break;
            case 'l':
                config->use_btl = true;
                break;
            case '4':
                config->use_bt4 = true;
                break;
            case '5':
                config->use_bt5 = true;
                break;
            case 'p':
                config->use_packs = true;
                break;
            case 'g':
                config->use_gps = true;
                break;
            default:
                break;
        }
    }
    if (config->use_beacon)
        printf("\nReminder: Wi-Fi Beacon only works when running\n\"sudo hostapd/hostapd/hostapd beacon.conf\" in a separate shell.\n\n");
    if (config->use_beacon && !config->use_packs)
        printf("\nWarning: Transmitting single messages on Wi-Fi beacon is violating\nthe standards. Enable message packs.\n\n");

    if (config->use_btl && (config->use_bt4 || config->use_bt5)) {
        printf("\nError: Cannot use both old API and Extended Advertising API at the same time.\n\n");
        exit(EXIT_FAILURE);
    }
    if ((config->use_btl || config->use_bt4) && config->use_packs) {
        printf("\nError: BT4 cannot use message packs.\n\n");
        exit(EXIT_FAILURE);
    }
    if (config->use_bt4 && config->use_bt5)
        printf("\nWarning: Doing simultaneous BT4 and BT5 will not necessarily work.\n\n");
    if (config->use_bt5 && !config->use_packs)
        printf("\nWarning: Transmitting single messages on Bluetooth 5 Long Range is violating\nthe standards. Enable message packs.\n\n");

    if (!config->use_beacon && !config->use_btl && !config->use_bt4 && !config->use_bt5) {
        print_help();
        exit(EXIT_SUCCESS);
    }

    if (config->use_gps)
        printf("\nWarning: Fetching GPS data requires a configured GPS sensor.\n\n");
}

void gps_loop(struct gps_loop_args *args) {
    struct gps_data_t *gpsdata = args->gpsdata;
    struct ODID_UAS_Data *uasData = args->uasData;

    char gpsd_message[GPS_JSON_RESPONSE_MAX];
    int retries = 0;      // cycles to wait before gpsd timeout
    int read_retries = 0;
    while(true) {
        if(kill_program)
            break;

        int ret;
        ret = gps_waiting(gpsdata, GPS_WAIT_TIME_MICROSECS);
        if (!ret) {
            printf("Socket not ready, retrying...\n");
            if (retries++ > MAX_GPS_WAIT_RETRIES) {
                    fprintf(stderr, "Max socket wait retries reached, exiting...");
                kill_program = true;
                args->exit_status = 1;
                pthread_exit((void*) &args->exit_status);
            }
            continue;
        } else {
            retries = 0;
            gpsd_message[0] = '\0';

            if (gps_read(gpsdata, gpsd_message, sizeof(gpsd_message)) == -1) {
                printf("Failed to read from socket, retrying...\n");
                if(read_retries++ > MAX_GPS_READ_RETRIES) {
                    fprintf(stderr, "Max socket read retries reached, exiting...");
                    kill_program = true;
                    args->exit_status = 1;
                    pthread_exit((void*) &args->exit_status);
                }
                continue;
            }
            read_retries = 0;

            process_gps_data(gpsdata, uasData);
        }
    }

    args->exit_status = 0;
    pthread_exit(&args->exit_status);
}

int main(int argc, char *argv[])
{
    parse_command_line(argc, argv, &config);

    config.handle_bt4 = 0; // The Extended Advertising set number used for BT4
    config.handle_bt5 = 1; // The Extended Advertising set number used for BT5

    if (config.use_beacon) {
        sem_init(&semaphore,0,0);
        pthread_create(&id, NULL, ap_interface_init, NULL);
        sem_wait(&semaphore);
    }

    struct ODID_UAS_Data uasData;
    odid_initUasData(&uasData);
    fill_example_data(&uasData);
    if(!config.use_gps)
        fill_example_gps_data(&uasData);
    int ret;
    ECDSA_SIG *sig;
    EC_KEY *eckey=EC_KEY_new_by_curve_name(NID_secp256k1);
    EC_KEY_generate_key(eckey);
    EC_POINT* pub_key = (EC_POINT *)EC_KEY_get0_public_key(eckey);
    EC_GROUP* secp256k1_group = EC_GROUP_new_by_curve_name(NID_secp256k1);
	char* pub_key_char    = EC_POINT_point2hex(secp256k1_group, pub_key, POINT_CONVERSION_COMPRESSED, NULL);
    EC_GROUP_free(secp256k1_group);
    printf("Public key: %s\n", pub_key_char);
    sign_data(&uasData, eckey);

    // CODE TO VERIFY SIGNATURE FROM IMPORTED BYTES
    // EC_KEY* imported_key_pair = EC_KEY_new_by_curve_name(NID_secp256k1);
    // EC_GROUP* curve_group       = EC_GROUP_new_by_curve_name(NID_secp256k1);
    // EC_POINT* public_point      = EC_POINT_new(curve_group);
    // public_point      = EC_POINT_hex2point(curve_group, pub_key_char, public_point, nullptr);
    // EC_KEY_set_public_key(imported_key_pair, public_point);
    // EC_GROUP_free(curve_group);
    // EC_POINT_free(public_point);
    // free(pub_key_char);
    // bool verification = ECDSA_verify(0, digest, SHA256_DIGEST_LENGTH, signature, signature_len, imported_key_pair);
    // if (verification == 1)
    //     printf("Re-Verification successful\n");
    // else
    //     printf("Re-Verification NOT successful\n");
    // EC_KEY_free(imported_key_pair);

    if (config.use_btl || config.use_bt4 || config.use_bt5)
        init_bluetooth(&config);

    if(config.use_gps) {
        signal(SIGINT,  sig_handler);
        signal(SIGKILL, sig_handler);
        signal(SIGSTOP, sig_handler);
        signal(SIGTERM, sig_handler);

        if(init_gps(&source, &gpsdata) != 0) {
            fprintf(stderr,
                    "No gpsd running or network error: %d, %s\n",
                    errno, gps_errstr(errno));
            cleanup(EXIT_FAILURE);
        }

        struct gps_loop_args args;
        args.gpsdata = &gpsdata;
        args.uasData = &uasData;
        pthread_create(&gps_thread, NULL, (void*) &gps_loop, &args);

        while (true)
        {
            if(kill_program)
                break;

            printf("Transmitting...\n");
            if (config.use_packs)
                send_packs(&uasData, &config);
            else
                send_single_messages(&uasData, &config);
        }
    } else {
        if (config.use_packs)
            send_packs(&uasData, &config);
        else
            send_single_messages(&uasData, &config);
    }

    cleanup(EXIT_SUCCESS);
}

