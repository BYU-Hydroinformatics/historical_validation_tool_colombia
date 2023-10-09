// ------------------------------------------------------------------------------------------------------------ //
//                                    DATA ON LOCALITIES AND BASIN DISTRICTS                                    //
// ------------------------------------------------------------------------------------------------------------ //

// Departments
let loc = [
    {name : "Colómbia" , file : "COLOMBIA.json"},
    {name : "Amazonas" , file : "Amazonas.json"},
    {name : "Bogotá D. C." , file : "Bogota_DC.json"},
    {name : "Caldas" , file : "Caldas.json"},
    {name : "Cesar" , file : "Cesar.json"},
    {name : "Guainía" , file : "Guainia.json"},
    {name : "Magdalena" , file : "Magdalena.json"},
    {name : "Putumayo" , file : "Putumayo.json"},
    {name : "Sucre" , file : "Sucre.json"},
    {name : "Vichada" , file : "Vichada.json"},
    {name : "Antíoquia" , file : "Antioquia.json"},
    {name : "Bolívar" , file : "Bolivar.json"},
    {name : "Caquetá" , file : "Caqueta.json"},
    {name : "Chocó" , file : "Choco.json"},
    {name : "Guaviare" , file : "Guaviare.json"},
    {name : "Meta" , file : "Meta.json"},
    {name : "Quindío" , file : "Quindio.json"},
    {name : "Tolima" , file : "Tolima.json"},
    {name : "Arauca" , file : "Arauca.json"},
    {name : "Boyacá" , file : "Boyaca.json"},
    {name : "Casanare" , file : "Casanare.json"},
    {name : "Córdoba" , file : "Cordoba.json"},
    {name : "Huíla" , file : "Huila.json"},
    {name : "Nariño" , file : "Narino.json"},
    {name : "Risalda" , file : "Risaralda.json"},
    {name : "Valle del Cauca" , file : "Valle_del_Cauca.json"},
    {name : "Atlántico" , file : "Atlantico.json"},
    {name : "Cauca" , file : "Cauca.json"},
    {name : "Cundinamarca" , file : "Cundinamarca.json"},
    {name : "La Guajira" , file : "La_Guajira.json"},
    {name : "Norte de Santander" , file : "Norte_de_Santander.json"},
    {name : "Santander" , file : "Santander.json"},
    {name : "Vaupés" , file : "Vaupes.json"},
];

// Hydrologic zone
let hyz = [
    {name : "Colombia", file : "COLOMBIA.json"},
    {name : "12 Caribe Litoral", file : "12_Caribe_Litoral.json"},
    {name : "55 Baudo Directos Pacifico", file : "55_Baudo_Directos_Pacifico.json"},
    {name : "49 Napo", file : "49_Napo.json"},
    {name : "11 Atrato Darien", file : "11_Atrato_Darien.json"},
    {name : "44 Caqueta", file : "44_Caqueta.json"},
    {name : "36 Casanare", file : "36_Casanare.json"},
    {name : "27 Nechi", file : "27_Nechi.json"},
    {name : "24 Sogamoso", file : "24_Sogamoso.json"},
    {name : "46 Caguan", file : "46_Caguan.json"},
    {name : "29 Bajo Magdalena", file : "29_Bajo_Magdalena.json"},
    {name : "25 Bajo Magdalena Cauca San Jorge", file : "25_Bajo_Magdalena_Cauca_San_Jorge.json"},
    {name : "16 Catatumbo", file : "16_Catatumbo.json"},
    {name : "38 Orinoco Directos", file : "38_Orinoco_Directos.json"},
    {name : "54 San Juan", file : "54_San_Juan.json"},
    {name : "28 Cesar", file : "28_Cesar.json"},
    {name : "23 Medio Magdalena", file : "23_Medio_Magdalena.json"},
    {name : "48 Amazonas Directos", file : "48_Amazonas_Directos.json"},
    {name : "45 Yari", file : "45_Yari.json"},
    {name : "21 Alto Magdalena", file : "21_Alto_Magdalena.json"},
    {name : "26 Cauca", file : "26_Cauca.json"},
    {name : "53 Tapaje Dagua Directos", file : "53_Tapaje_Dagua_Directos.json"},
    {name : "15 Caribe Guajira", file : "15_Caribe_Guajira.json"},
    {name : "31 Inirida", file : "31_Inirida.json"},
    {name : "51 Mira", file : "51_Mira.json"},
    {name : "47 Putumayo", file : "47_Putumayo.json"},
    {name : "52 Patia", file : "52_Patia.json"},
    {name : "43 Apaporis", file : "43_Apaporis.json"},
    {name : "34 Tomo", file : "34_Tomo.json"},
    {name : "33 Vichada", file : "33_Vichada.json"},
    {name : "42 Vaupes", file : "42_Vaupes.json"},
    {name : "13 Sinu", file : "13_Sinu.json"},
    {name : "41 Guainia", file : "41_Guainia.json"},
    {name : "37 Arauca", file : "37_Arauca.json"},
    {name : "57 Rio Tuira", file : "57_Rio_Tuira.json"},
    {name : "17 Islas Caribe", file : "17_Islas_Caribe.json"},
    {name : "35 Meta", file : "35_Meta.json"},
    {name : "22 Saldana", file : "22_Saldana.json"},
    {name : "32 Guaviare", file : "32_Guaviare.json"},
    {name : "56 Pacifico Directos", file : "56_Pacifico_Directos.json"},
    {name : "39 Apure", file : "39_Apure.json"},
];

// Hydrologic sub zone
let subhyz = [
    {name : "Colombia", file : "COLOMBIA.json"},
    {name : "3201 Rio Guayabero Alto", file : "3201_Rio_Guayabero_Alto.json"},
    {name : "5206 Rio Telembi", file : "5206_Rio_Telembi.json"},
    {name : "2321 Quebrada El Carmen y Otros Directos al Magdalena", file : "2321_Quebrada_El_Carmen_y_Otros_Directos_al_Magdalena.json"},
    {name : "5101 Rio San Juan Frontera Ecuador", file : "5101_Rio_San_Juan_Frontera_Ecuador.json"},
    {name : "2605 Rio Timba", file : "2605_Rio_Timba.json"},
    {name : "1106 Directos Atrato entre rios Bebarama y Murri", file : "1106_Directos_Atrato_entre_rios_Bebarama_y_Murri.json"},
    {name : "4604 Rio Caguan Bajo", file : "4604_Rio_Caguan_Bajo.json"},
    {name : "5310 Rio Anchicaya", file : "5310_Rio_Anchicaya.json"},
    {name : "5408 Rio San Juan Medio", file : "5408_Rio_San_Juan_Medio.json"},
    {name : "1101 Rio Andagueda", file : "1101_Rio_Andagueda.json"},
    {name : "3511 Directos al Meta entre rios Guayuriba y Yucao", file : "3511_Directos_al_Meta_entre_rios_Guayuriba_y_Yucao.json"},
    {name : "3701 Rio Chitaga", file : "3701_Rio_Chitaga.json"},
    {name : "3605 Rio Agua Clara", file : "3605_Rio_Agua_Clara.json"},
    {name : "1504 Rio Tapias", file : "1504_Rio_Tapias.json"},
    {name : "4701 Alto Rio Putumayo", file : "4701_Alto_Rio_Putumayo.json"},
    {name : "1111 Rio Sucio", file : "1111_Rio_Sucio.json"},
    {name : "5401 Rio San Juan Alto", file : "5401_Rio_San_Juan_Alto.json"},
    {name : "2116 Rio Prado", file : "2116_Rio_Prado.json"},
    {name : "2701 Rio Porce", file : "2701_Rio_Porce.json"},
    {name : "3506 Rio Guavio", file : "3506_Rio_Guavio.json"},
    {name : "2804 Rio Ariguani", file : "2804_Rio_Ariguani.json"},
    {name : "2122 Rio Opia y otros Directos al Magdalena", file : "2122_Rio_Opia_y_otros_Directos_al_Magdalena.json"},
    {name : "2612 Rio La Vieja", file : "2612_Rio_La_Vieja.json"},
    {name : "4417 Rio Cahuinari", file : "4417_Rio_Cahuinari.json"},
    {name : "2121 Rio Coello", file : "2121_Rio_Coello.json"},
    {name : "3403 Bajo Rio Tomo", file : "3403_Bajo_Rio_Tomo.json"},
    {name : "5305 Rio Timbiqui", file : "5305_Rio_Timbiqui.json"},
    {name : "2617 Rio Cartama y otros Directos al Cauca", file : "2617_Rio_Cartama_y_otros_Directos_al_Cauca.json"},
    {name : "2204 Rio Amoya", file : "2204_Rio_Amoya.json"},
    {name : "4601 Rio Caguan Alto", file : "4601_Rio_Caguan_Alto.json"},
    {name : "2902 Directos al Bajo Magdalena entre El Plato y Calamar", file : "2902_Directos_al_Bajo_Magdalena_entre_El_Plato_y_Calamar.json"},
    {name : "3108 R Inirida hasta bocas Cano Bocon y R Las Vinas", file : "3108_R_Inirida_hasta_bocas_Cano_Bocon_y_R_Las_Vinas.json"},
    {name : "2304 Directos Magdalena entre Rios Guarino y La Miel", file : "2304_Directos_Magdalena_entre_Rios_Guarino_y_La_Miel.json"},
    {name : "2608 Rios Pescador RUT Chanco Catarina y Canaveral", file : "2608_Rios_Pescador_RUT_Chanco_Catarina_y_Canaveral.json"},
    {name : "2303 Directos al Magdalena entre Rios Seco y Negro", file : "2303_Directos_al_Magdalena_entre_Rios_Seco_y_Negro.json"},
    {name : "4101 Alto Rio Guainia", file : "4101_Alto_Rio_Guainia.json"},
    {name : "5406 Rio Munguido", file : "5406_Rio_Munguido.json"},
    {name : "5308 Rio Naya Yurumangui", file : "5308_Rio_Naya_Yurumangui.json"},
    {name : "2102 Rio Timana y otros directos al Magdalena", file : "2102_Rio_Timana_y_otros_directos_al_Magdalena.json"},
    {name : "3210 Medio Guaviare", file : "3210_Medio_Guaviare.json"},
    {name : "5304 Rio Guapi", file : "5304_Rio_Guapi.json"},
    {name : "2119 Rio Sumapaz", file : "2119_Rio_Sumapaz.json"},
    {name : "4801 Directos Rio Amazonas", file : "4801_Directos_Rio_Amazonas.json"},
    {name : "4408 Rio Mecaya", file : "4408_Rio_Mecaya.json"},
    {name : "2615 Rio Chinchina", file : "2615_Rio_Chinchina.json"},
    {name : "2603 Rio Salado y otros directos Cauca", file : "2603_Rio_Salado_y_otros_directos_Cauca.json"},
    {name : "3603 Rio Cravo Norte", file : "3603_Rio_Cravo_Norte.json"},
    {name : "1110 Rio Murindo Directos al Atrato", file : "1110_Rio_Murindo_Directos_al_Atrato.json"},
    {name : "3512 Rio Yucao", file : "3512_Rio_Yucao.json"},
    {name : "2909 Cienaga Mallorquin", file : "2909_Cienaga_Mallorquin.json"},
    {name : "3602 Rio Casanare", file : "3602_Rio_Casanare.json"},
    {name : "3601 Rio Ariporo", file : "3601_Rio_Ariporo.json"},
    {name : "1303 Bajo Sinu", file : "1303_Bajo_Sinu.json"},
    {name : "2630 Rios Lili Melendez y Canaveralejo", file : "2630_Rios_Lili_Melendez_y_Canaveralejo.json"},
    {name : "4707 Rio Igara Parana", file : "4707_Rio_Igara_Parana.json"},
    {name : "4302 Rio Ajaju", file : "4302_Rio_Ajaju.json"},
    {name : "4504 Medio Yari", file : "4504_Medio_Yari.json"},
    {name : "3203 Rio Losada", file : "3203_Rio_Losada.json"},
    {name : "4501 Alto Yari", file : "4501_Alto_Yari.json"},
    {name : "1103 Rio Quito", file : "1103_Rio_Quito.json"},
    {name : "3801 Rio Vita", file : "3801_Rio_Vita.json"},
    {name : "4108 Rio Cuiary", file : "4108_Rio_Cuiary.json"},
    {name : "3503 Rio Guatiquia", file : "3503_Rio_Guatiquia.json"},
    {name : "2606 Rio Ovejas", file : "2606_Rio_Ovejas.json"},
    {name : "2206 Rio Tetuan Rio Ortega", file : "2206_Rio_Tetuan_Rio_Ortega.json"},
    {name : "3803 Cano Mataven y otros Directos al Orinoco", file : "3803_Cano_Mataven_y_otros_Directos_al_Orinoco.json"},
    {name : "5202 Rio San Jorge", file : "5202_Rio_San_Jorge.json"},
    {name : "2103 Rio Suaza", file : "2103_Rio_Suaza.json"},
    {name : "3218 Bajo Rio Uva", file : "3218_Bajo_Rio_Uva.json"},
    {name : "1202 Rio Mulatos y otros directos al Caribe", file : "1202_Rio_Mulatos_y_otros_directos_al_Caribe.json"},
    {name : "3212 Rio Siare", file : "3212_Rio_Siare.json"},
    {name : "2801 Alto Cesar", file : "2801_Alto_Cesar.json"},
    {name : "3107 Cano Nabuquen", file : "3107_Cano_Nabuquen.json"},
    {name : "4710 Rio Cotuhe", file : "4710_Rio_Cotuhe.json"},
    {name : "5402 Rio Tamana y otros Directos San Juan", file : "5402_Rio_Tamana_y_otros_Directos_San_Juan.json"},
    {name : "2805 Bajo Cesar", file : "2805_Bajo_Cesar.json"},
    {name : "3514 Cano Cumaral", file : "3514_Cano_Cumaral.json"},
    {name : "3306 Bajo Vichada", file : "3306_Bajo_Vichada.json"},
    {name : "4301 Rio Tunia o Macaya", file : "4301_Rio_Tunia_o_Macaya.json"},
    {name : "2501 Alto San Jorge", file : "2501_Alto_San_Jorge.json"},
    {name : "4403 Rio Orteguaza", file : "4403_Rio_Orteguaza.json"},
    {name : "3519 Rio Cusiana", file : "3519_Rio_Cusiana.json"},
    {name : "4402 Rio Caqueta Medio", file : "4402_Rio_Caqueta_Medio.json"},
    {name : "4102 Medio Rio Guainia", file : "4102_Medio_Rio_Guainia.json"},
    {name : "2637 Quebradas Las Canas Los Micos y Obando", file : "2637_Quebradas_Las_Canas_Los_Micos_y_Obando.json"},
    {name : "2311 Directos al Magdalena Medio entre rios Negro", file : "2311_Directos_al_Magdalena_Medio_entre_rios_Negro.json"},
    {name : "2628 Rio Quinamayo y otros directos al Cauca", file : "2628_Rio_Quinamayo_y_otros_directos_al_Cauca.json"},
    {name : "2319 Rio Lebrija y otros directos al Magdalena", file : "2319_Rio_Lebrija_y_otros_directos_al_Magdalena.json"},
    {name : "4502 Rio Camuya", file : "4502_Rio_Camuya.json"},
    {name : "4209 Rio Papuri", file : "4209_Rio_Papuri.json"},
    {name : "1602 Rio Zulia", file : "1602_Rio_Zulia.json"},
    {name : "4306 Rio Cananari", file : "4306_Rio_Cananari.json"},
    {name : "4202 Rio Unilla", file : "4202_Rio_Unilla.json"},
    {name : "2607 Rio Guachal Bolo Fraile y Parraga", file : "2607_Rio_Guachal_Bolo_Fraile_y_Parraga.json"},
    {name : "2502 Bajo San Jorge La Mojana", file : "2502_Bajo_San_Jorge_La_Mojana.json"},
    {name : "3527 Directos al Rio Meta entre rios Guatiquia y Upia", file : "3527_Directos_al_Rio_Meta_entre_rios_Guatiquia_y_Upia.json"},
    {name : "1506 Rio Rancheria", file : "1506_Rio_Rancheria.json"},
    {name : "3604 Cano Samuco", file : "3604_Cano_Samuco.json"},
    {name : "3207 Rio Guejar", file : "3207_Rio_Guejar.json"},
    {name : "4704 Rio Putumayo Directos", file : "4704_Rio_Putumayo_Directos.json"},
    {name : "2314 Rio Opon", file : "2314_Rio_Opon.json"},
    {name : "2610 Rios Tulua y Morales", file : "2610_Rios_Tulua_y_Morales.json"},
    {name : "3405 Cano Lioni o Terecay", file : "3405_Cano_Lioni_o_Terecay.json"},
    {name : "4305 Bajo Rio Apaporis", file : "4305_Bajo_Rio_Apaporis.json"},
    {name : "3524 Directos al Rio Meta entre rios Pauto y Agua Clara", file : "3524_Directos_al_Rio_Meta_entre_rios_Pauto_y_Agua_Clara.json"},
    {name : "2907 Directos Bajo Magdalena entre El Banco y El Plato", file : "2907_Directos_Bajo_Magdalena_entre_El_Banco_y_El_Plato.json"},
    {name : "4201 Rio Itilla", file : "4201_Rio_Itilla.json"},
    {name : "3303 Rio Muco", file : "3303_Rio_Muco.json"},
    {name : "2302 Rio Guarino", file : "2302_Rio_Guarino.json"},
    {name : "3101 Rio Inirida Alto", file : "3101_Rio_Inirida_Alto.json"},
    {name : "2123 Rio Seco y otros Directos al Magdalena", file : "2123_Rio_Seco_y_otros_Directos_al_Magdalena.json"},
    {name : "5309 Rios Cajambre Mayorquin Raposo", file : "5309_Rios_Cajambre_Mayorquin_Raposo.json"},
    {name : "5205 Rio Guaitara", file : "5205_Rio_Guaitara.json"},
    {name : "2108 Rio Yaguara y Rio Iquira", file : "2108_Rio_Yaguara_y_Rio_Iquira.json"},
    {name : "2631 Rios Arroyohondo Yumbo Mulalo Vijes Yotoco", file : "2631_Rios_Arroyohondo_Yumbo_Mulalo_Vijes_Yotoco.json"},
    {name : "1204 Rio Canalete y otros Arroyos Directos al Caribe", file : "1204_Rio_Canalete_y_otros_Arroyos_Directos_al_Caribe.json"},
    {name : "3509 Rio Upia", file : "3509_Rio_Upia.json"},
    {name : "2207 Rio Cucuana", file : "2207_Rio_Cucuana.json"},
    {name : "2305 Rio La Miel Samana", file : "2305_Rio_La_Miel_Samana.json"},
    {name : "4401 Alto Caqueta", file : "4401_Alto_Caqueta.json"},
    {name : "2320 Directos al Magdalena Brazo Morales", file : "2320_Directos_al_Magdalena_Brazo_Morales.json"},
    {name : "1203 Rio San Juan", file : "1203_Rio_San_Juan.json"},
    {name : "5201 Rio Patia Alto", file : "5201_Rio_Patia_Alto.json"},
    {name : "3502 Rio Guayuriba", file : "3502_Rio_Guayuriba.json"},
    {name : "2601 Alto Rio Cauca", file : "2601_Alto_Rio_Cauca.json"},
    {name : "2118 Rio Luisa y otros directos al Magdalena", file : "2118_Rio_Luisa_y_otros_directos_al_Magdalena.json"},
    {name : "2120 Rio Bogota", file : "2120_Rio_Bogota.json"},
    {name : "1701 San Andres", file : "1701_San_Andres.json"},
    {name : "2802 Medio Cesar", file : "2802_Medio_Cesar.json"},
    {name : "2208 Bajo Saldana", file : "2208_Bajo_Saldana.json"},
    {name : "1107 Rio Murri", file : "1107_Rio_Murri.json"},
    {name : "1104 Rio Bebarama y otros Directos Atrato", file : "1104_Rio_Bebarama_y_otros_Directos_Atrato.json"},
    {name : "3901 Alto Rio Apure", file : "3901_Alto_Rio_Apure.json"},
    {name : "4706 Rio Putumayo Bajo", file : "4706_Rio_Putumayo_Bajo.json"},
    {name : "2626 Directos Bajo Cauca Cga La Raya entre rio Nechi", file : "2626_Directos_Bajo_Cauca_Cga_La_Raya_entre_rio_Nechi.json"},
    {name : "2625 Directos al Cauca entre Pto Valdivia y Rio Nechi", file : "2625_Directos_al_Cauca_entre_Pto_Valdivia_y_Rio_Nechi.json"},
    {name : "3702 Rio Margua", file : "3702_Rio_Margua.json"},
    {name : "4109 Rio Isana", file : "4109_Rio_Isana.json"},
    {name : "1505 Rio Camarones y otros directos Caribe", file : "1505_Rio_Camarones_y_otros_directos_Caribe.json"},
    {name : "2632 Rios Guabas Zabaletas y Sonso", file : "2632_Rios_Guabas_Zabaletas_y_Sonso.json"},
    {name : "2308 Rio Nare", file : "2308_Rio_Nare.json"},
    {name : "3804 Directos Rio Atabapo", file : "3804_Directos_Rio_Atabapo.json"},
    {name : "2301 Rio Guali", file : "2301_Rio_Guali.json"},
    {name : "3501 Rio Metica Guamal Humadea", file : "3501_Rio_Metica_Guamal_Humadea.json"},
    {name : "2903 Canal del Dique margen derecho", file : "2903_Canal_del_Dique_margen_derecho.json"},
    {name : "2901 Directos al Bajo Magdalena entre El Plato y Calamar", file : "2901_Directos_al_Bajo_Magdalena_entre_El_Plato_y_Calamar.json"},
    {name : "5204 Rio Juananbu", file : "5204_Rio_Juananbu.json"},
    {name : "3513 Rio Melua", file : "3513_Rio_Melua.json"},
    {name : "4303 Alto Rio Apaporis", file : "4303_Alto_Rio_Apaporis.json"},
    {name : "2201 Alto Saldana", file : "2201_Alto_Saldana.json"},
    {name : "5404 Rio Cajon", file : "5404_Rio_Cajon.json"},
    {name : "2105 Rio Paez", file : "2105_Rio_Paez.json"},
    {name : "1115 Rio Tanela y otros Directos al Atrato", file : "1115_Rio_Tanela_y_otros_Directos_al_Atrato.json"},
    {name : "5209 Rio Patia Bajo", file : "5209_Rio_Patia_Bajo.json"},
    {name : "1206 Arroyos Directos al Caribe", file : "1206_Arroyos_Directos_al_Caribe.json"},
    {name : "3510 Rio Negro", file : "3510_Rio_Negro.json"},
    {name : "4510 Rio Mesay", file : "4510_Rio_Mesay.json"},
    {name : "2306 Rio Negro", file : "2306_Rio_Negro.json"},
    {name : "1606 Rio Socuavo del Norte y Rio Socuavo Sur", file : "1606_Rio_Socuavo_del_Norte_y_Rio_Socuavo_Sur.json"},
    {name : "2202 Rio Ata", file : "2202_Rio_Ata.json"},
    {name : "5104 Rio Chagui", file : "5104_Rio_Chagui.json"},
    {name : "4711 Rio Purite", file : "4711_Rio_Purite.json"},
    {name : "4420 Rio Pure", file : "4420_Rio_Pure.json"},
    {name : "4404 Rio Pescado", file : "4404_Rio_Pescado.json"},
    {name : "3206 Rio Ariari", file : "3206_Rio_Ariari.json"},
    {name : "3518 Rio Tua y otros Directos al Meta", file : "3518_Rio_Tua_y_otros_Directos_al_Meta.json"},
    {name : "2618 Rio Arma", file : "2618_Rio_Arma.json"},
    {name : "4208 Rio Querary", file : "4208_Rio_Querary.json"},
    {name : "4415 Rio Caqueta Bajo", file : "4415_Rio_Caqueta_Bajo.json"},
    {name : "3516 Lago de Tota", file : "3516_Lago_de_Tota.json"},
    {name : "2634 Rio Cali", file : "2634_Rio_Cali.json"},
    {name : "2602 Rio Palace", file : "2602_Rio_Palace.json"},
    {name : "2106 Rios directos Magdalena", file : "2106_Rios_directos_Magdalena.json"},
    {name : "4410 Rio Peneya", file : "4410_Rio_Peneya.json"},
    {name : "3104 Rio Inirida Medio", file : "3104_Rio_Inirida_Medio.json"},
    {name : "3217 Medio Rio Uva", file : "3217_Medio_Rio_Uva.json"},
    {name : "2609 Rios Amaime y Cerrito", file : "2609_Rios_Amaime_y_Cerrito.json"},
    {name : "2906 Cga Grande de Santa Marta", file : "2906_Cga_Grande_de_Santa_Marta.json"},
    {name : "2110 Rio Neiva", file : "2110_Rio_Neiva.json"},
    {name : "2627 Rio Piendamo", file : "2627_Rio_Piendamo.json"},
    {name : "3204 Rio Guayabero Bajo", file : "3204_Rio_Guayabero_Bajo.json"},
    {name : "1109 Rio Napipi Rio Opogado", file : "1109_Rio_Napipi_Rio_Opogado.json"},
    {name : "5311 Dagua Buenaventura Bahia Malaga", file : "5311_Dagua_Buenaventura_Bahia_Malaga.json"},
    {name : "1502 Rio Don Diego", file : "1502_Rio_Don_Diego.json"},
    {name : "1112 Rio Salaqui y otros directos Bajo Atrato", file : "1112_Rio_Salaqui_y_otros_directos_Bajo_Atrato.json"},
    {name : "1509 Rio Guachaca Mendiguaca y Buritaca", file : "1509_Rio_Guachaca_Mendiguaca_y_Buritaca.json"},
    {name : "3515 Rio Manacacias y otros Directos al Meta", file : "3515_Rio_Manacacias_y_otros_Directos_al_Meta.json"},
    {name : "3504 Rio Guacavia", file : "3504_Rio_Guacavia.json"},
    {name : "4409 Rio Sencella", file : "4409_Rio_Sencella.json"},
    {name : "2624 Rio Taraza Rio Man", file : "2624_Rio_Taraza_Rio_Man.json"},
    {name : "3706 Directos Rio Arauca", file : "3706_Directos_Rio_Arauca.json"},
    {name : "4207 Bajo Vaupes", file : "4207_Bajo_Vaupes.json"},
    {name : "1501 Rio Piedras Rio Manzanares", file : "1501_Rio_Piedras_Rio_Manzanares.json"},
    {name : "4509 Rio Cunare", file : "4509_Rio_Cunare.json"},
    {name : "4110 Rio Tomo", file : "4110_Rio_Tomo.json"},
    {name : "2613 Rio Otun y otros directos al Cauca", file : "2613_Rio_Otun_y_otros_directos_al_Cauca.json"},
    {name : "3520 Directos al Meta entre rios Cusiana y Cravo Sur", file : "3520_Directos_al_Meta_entre_rios_Cusiana_y_Cravo_Sur.json"},
    {name : "1205 Directos Caribe Golfo de Morrosquillo", file : "1205_Directos_Caribe_Golfo_de_Morrosquillo.json"},
    {name : "1117 Rio Cabi y otros Directos Atrato", file : "1117_Rio_Cabi_y_otros_Directos_Atrato.json"},
    {name : "2904 Directos al Bajo Magdalena entre Calamar y desembocadura", file : "2904_Directos_al_Bajo_Magdalena_entre_Calamar_y_desembocadura.json"},
    {name : "3214 Bajo Guaviare", file : "3214_Bajo_Guaviare.json"},
    {name : "5403 Rio Sipi", file : "5403_Rio_Sipi.json"},
    {name : "3302 Rio Guarrojo", file : "3302_Rio_Guarrojo.json"},
    {name : "2702 Alto Nechi", file : "2702_Alto_Nechi.json"},
    {name : "3305 Directos Vichada Medio", file : "3305_Directos_Vichada_Medio.json"},
    {name : "4307 Rio Pira Parana", file : "4307_Rio_Pira_Parana.json"},
    {name : "3505 Rio Humea", file : "3505_Rio_Humea.json"},
    {name : "2111 Rio Fortalecillas y otros", file : "2111_Rio_Fortalecillas_y_otros.json"},
    {name : "2403 Rio Chicamocha", file : "2403_Rio_Chicamocha.json"},
    {name : "5701 Rio Tuira", file : "5701_Rio_Tuira.json"},
    {name : "5203 Rio Mayo", file : "5203_Rio_Mayo.json"},
    {name : "2112 Rio Bache", file : "2112_Rio_Bache.json"},
    {name : "2307 Directos Magdalena Medio entre rios La Miel y Nare", file : "2307_Directos_Magdalena_Medio_entre_rios_La_Miel_y_Nare.json"},
    {name : "3215 Cano Minisiare", file : "3215_Cano_Minisiare.json"},
    {name : "4407 Rio Rutuya", file : "4407_Rio_Rutuya.json"},
    {name : "5407 Rios Calima y Bajo San Juan", file : "5407_Rios_Calima_y_Bajo_San_Juan.json"},
    {name : "3110 Cano Bocon", file : "3110_Cano_Bocon.json"},
    {name : "2614 Rio Risaralda", file : "2614_Rio_Risaralda.json"},
    {name : "5103 Rio Rosario", file : "5103_Rio_Rosario.json"},
    {name : "4309 Directos Rio Taraira", file : "4309_Directos_Rio_Taraira.json"},
    {name : "3213 Rio Iteviare", file : "3213_Rio_Iteviare.json"},
    {name : "2703 Bajo Nechi", file : "2703_Bajo_Nechi.json"},
    {name : "4211 Rio Tiquie", file : "4211_Rio_Tiquie.json"},
    {name : "1508 Rio Carraipia Paraguachon Directos al Golfo Maracaibo", file : "1508_Rio_Carraipia_Paraguachon_Directos_al_Golfo_Maracaibo.json"},
    {name : "4107 Directos Rio Negro", file : "4107_Directos_Rio_Negro.json"},
    {name : "2203 Medio Saldana", file : "2203_Medio_Saldana.json"},
    {name : "5306 Rio Saija", file : "5306_Rio_Saija.json"},
    {name : "3507 Rio Garagoa", file : "3507_Rio_Garagoa.json"},
    {name : "2101 Alto Magdalena", file : "2101_Alto_Magdalena.json"},
    {name : "5405 Rio Capoma y otros directos al San Juan", file : "5405_Rio_Capoma_y_otros_directos_al_San_Juan.json"},
    {name : "5601 Directos Pacifico Frontera Panama", file : "5601_Directos_Pacifico_Frontera_Panama.json"},
    {name : "2125 Rio Lagunilla y Otros Directos al Magdalena", file : "2125_Rio_Lagunilla_y_Otros_Directos_al_Magdalena.json"},
    {name : "4203 Alto Vaupes", file : "4203_Alto_Vaupes.json"},
    {name : "4702 Rio San Miguel", file : "4702_Rio_San_Miguel.json"},
    {name : "4602 Rio Guayas", file : "4602_Rio_Guayas.json"},
    {name : "1302 Medio Sinu", file : "1302_Medio_Sinu.json"},
    {name : "2109 Juncal y otros Rios directos al Magdalena", file : "2109_Juncal_y_otros_Rios_directos_al_Magdalena.json"},
    {name : "4705 Rio Cara Parana", file : "4705_Rio_Cara_Parana.json"},
    {name : "1108 Rio Bojaya", file : "1108_Rio_Bojaya.json"},
    {name : "3105 Rio Papunaya", file : "3105_Rio_Papunaya.json"},
    {name : "4505 Rio Luisa", file : "4505_Rio_Luisa.json"},
    {name : "4605 Rio Sunsiya", file : "4605_Rio_Sunsiya.json"},
    {name : "2124 Rio Totare", file : "2124_Rio_Totare.json"},
    {name : "2405 Rio Sogamoso", file : "2405_Rio_Sogamoso.json"},
    {name : "2619 Rio San Juan", file : "2619_Rio_San_Juan.json"},
    {name : "3704 Rio Bojaba y otros Directos al Arauca", file : "3704_Rio_Bojaba_y_otros_Directos_al_Arauca.json"},
    {name : "3301 Alto Vichada", file : "3301_Alto_Vichada.json"},
    {name : "5302 Rio Tapaje", file : "5302_Rio_Tapaje.json"},
    {name : "1607 Bajo Catatumbo", file : "1607_Bajo_Catatumbo.json"},
    {name : "4105 Bajo Rio Guainia", file : "4105_Bajo_Rio_Guainia.json"},
    {name : "2402 Rio Fonce", file : "2402_Rio_Fonce.json"},
    {name : "2114 Rio Cabrera", file : "2114_Rio_Cabrera.json"},
    {name : "3508 Rio Lengupa", file : "3508_Rio_Lengupa.json"},
    {name : "2908 Rios Chimicuica y Corozal", file : "2908_Rios_Chimicuica_y_Corozal.json"},
    {name : "1507 Directos Caribe Ay Sharimahana Alta Guajira", file : "1507_Directos_Caribe_Ay_Sharimahana_Alta_Guajira.json"},
    {name : "4506 Bajo Yari", file : "4506_Bajo_Yari.json"},
    {name : "1114 Directos Bajo Atrato entre rio Sucio y desembocadura", file : "1114_Directos_Bajo_Atrato_entre_rio_Sucio_y_desembocadura.json"},
    {name : "1601 Rio Pamplonita", file : "1601_Rio_Pamplonita.json"},
    {name : "5102 Rio Mira", file : "5102_Rio_Mira.json"},
    {name : "2629 Rios Claro y Jamundi", file : "2629_Rios_Claro_y_Jamundi.json"},
    {name : "4418 Rio Miriti Parana", file : "4418_Rio_Miriti_Parana.json"},
    {name : "5303 Rio Iscuande", file : "5303_Rio_Iscuande.json"},
    {name : "3401 Alto Rio Tomo", file : "3401_Alto_Rio_Tomo.json"},
    {name : "2905 Canal del Dique margen izquierda", file : "2905_Canal_del_Dique_margen_izquierda.json"},
    {name : "3525 Directos Bajo Meta entre rios Casanare y Orinoco", file : "3525_Directos_Bajo_Meta_entre_rios_Casanare_y_Orinoco.json"},
    {name : "1603 Rio Nuevo Presidente Tres Bocas Sardinata Tibu", file : "1603_Rio_Nuevo_Presidente_Tres_Bocas_Sardinata_Tibu.json"},
    {name : "4901 Rio Chingual", file : "4901_Rio_Chingual.json"},
    {name : "5502 Rio Docampado y Directos Pacifico", file : "5502_Rio_Docampado_y_Directos_Pacifico.json"},
    {name : "1503 Rio Ancho y Otros Directos al caribe", file : "1503_Rio_Ancho_y_Otros_Directos_al_caribe.json"},
    {name : "4106 Rio Aquio o Cano Aque", file : "4106_Rio_Aquio_o_Cano_Aque.json"},
    {name : "3703 Rio Cobugon Rio Cobaria", file : "3703_Rio_Cobugon_Rio_Cobaria.json"},
    {name : "2704 Directos al Bajo Nechi", file : "2704_Directos_al_Bajo_Nechi.json"},
    {name : "2604 Rio Palo", file : "2604_Rio_Palo.json"},
    {name : "2115 Directos Magdalena entre rios Cabrera y Sumapaz", file : "2115_Directos_Magdalena_entre_rios_Cabrera_y_Sumapaz.json"},
    {name : "3522 Cano Guanapalo y otros Directos al Meta", file : "3522_Cano_Guanapalo_y_otros_Directos_al_Meta.json"},
    {name : "1702 Providencia", file : "1702_Providencia.json"},
    {name : "2317 Rio Cimitarra y otros directos al Magdalena", file : "2317_Rio_Cimitarra_y_otros_directos_al_Magdalena.json"},
    {name : "1116 Rio Tolo y otros Directos al Caribe", file : "1116_Rio_Tolo_y_otros_Directos_al_Caribe.json"},
    {name : "2401 Rio Suarez", file : "2401_Rio_Suarez.json"},
    {name : "2616 Rio Tapias y otros directos al Cauca", file : "2616_Rio_Tapias_y_otros_directos_al_Cauca.json"},
    {name : "3705 Rio Banadia y otros Directos al Rio Arauca", file : "3705_Rio_Banadia_y_otros_Directos_al_Rio_Arauca.json"},
    {name : "2633 Rios Guadalajara y San Pedro", file : "2633_Rios_Guadalajara_y_San_Pedro.json"},
    {name : "2611 Rio Frio", file : "2611_Rio_Frio.json"},
    {name : "2113 Rio Aipe Rio Chenche y otros directos al Magdalena", file : "2113_Rio_Aipe_Rio_Chenche_y_otros_directos_al_Magdalena.json"},
    {name : "5307 Rio San Juan del Micay", file : "5307_Rio_San_Juan_del_Micay.json"},
    {name : "3202 Rio Guape", file : "3202_Rio_Guape.json"},
    {name : "3523 Rio Pauto y otros Directos al Meta", file : "3523_Rio_Pauto_y_otros_Directos_al_Meta.json"},
    {name : "2635 Rio Bugalagrande", file : "2635_Rio_Bugalagrande.json"},
    {name : "1608 Rio del Suroeste y directos Rio de Oro", file : "1608_Rio_del_Suroeste_y_directos_Rio_de_Oro.json"},
    {name : "1113 Rio Perancho", file : "1113_Rio_Perancho.json"},
    {name : "3521 Rio Cravo Sur", file : "3521_Rio_Cravo_Sur.json"},
    {name : "4414 Rio Cuemani", file : "4414_Rio_Cuemani.json"},
    {name : "4703 Rio Putumayo Medio", file : "4703_Rio_Putumayo_Medio.json"},
    {name : "3802 Rio Tuparro y otros Directos al Orinoco", file : "3802_Rio_Tuparro_y_otros_Directos_al_Orinoco.json"},
    {name : "2312 Rio Carare Minero", file : "2312_Rio_Carare_Minero.json"},
    {name : "1604 Rio Tarra", file : "1604_Rio_Tarra.json"},
    {name : "1102 Alto Atrato", file : "1102_Alto_Atrato.json"},
    {name : "1605 Rio Algodonal Alto Catatumbo", file : "1605_Rio_Algodonal_Alto_Catatumbo.json"},
    {name : "3805 Directos Orinoco entre rios Tomo y Meta", file : "3805_Directos_Orinoco_entre_rios_Tomo_y_Meta.json"},
    {name : "3526 Directos al Rio Meta entre rios Cusiana y Casanare", file : "3526_Directos_al_Rio_Meta_entre_rios_Cusiana_y_Casanare.json"},
    {name : "2104 Rios Directos al Magdalena", file : "2104_Rios_Directos_al_Magdalena.json"},
    {name : "5207 Rio Patia Medio", file : "5207_Rio_Patia_Medio.json"},
    {name : "2621 Directos Rio Cauca entre Rio San Juan y Pto Valdia", file : "2621_Directos_Rio_Cauca_entre_Rio_San_Juan_y_Pto_Valdia.json"},
    {name : "2310 Rio San Bartolo y otros directos al Magdalena Medio", file : "2310_Rio_San_Bartolo_y_otros_directos_al_Magdalena_Medio.json"},
    {name : "3216 Alto Rio Uva", file : "3216_Alto_Rio_Uva.json"},
    {name : "3809 Rio Cinaruco y Directos Rio Orinoco", file : "3809_Rio_Cinaruco_y_Directos_Rio_Orinoco.json"},
    {name : "1301 Alto Sinu Urra", file : "1301_Alto_Sinu_Urra.json"},
    {name : "1703 Roncador y Quitasueno", file : "1703_Roncador_y_Quitasueno.json"},
    {name : "2622 Rio Desbaratado", file : "2622_Rio_Desbaratado.json"},
    {name : "1105 Directos Atrato entre rios Quito y Bojaya", file : "1105_Directos_Atrato_entre_rios_Quito_y_Bojaya.json"},
    {name : "2636 Rio Paila", file : "2636_Rio_Paila.json"},
    {name : "1201 Rio Leon", file : "1201_Rio_Leon.json"},
    {name : "5501 Rio Baudo", file : "5501_Rio_Baudo.json"},
    {name : "3402 Rio Elvita", file : "3402_Rio_Elvita.json"},
    {name : "2620 Directos Rio Cauca entre Rio San Juan y Pto Valdivia", file : "2620_Directos_Rio_Cauca_entre_Rio_San_Juan_y_Pto_Valdivia.json"},
];

  
// ------------------------------------------------------------------------------------------------------------ //
//                                    DATA ON LOCALITIES AND BASIN DISTRICTS                                    //
// ------------------------------------------------------------------------------------------------------------ //

// Generate options for Localities
const loc_url = `${server}/static/historical_validation_tool_colombia/geojson/dep/`;
loc = loc.map((item) => {
    var option_custom = `<option value="${item.file}">${item.name}</option>`;
    return(option_custom);
  }).join("");

// Generate options for hydrological zones
const hyz_url = `${server}/static/historical_validation_tool_colombia/geojson/hydr_zone/`;
hyz = hyz.map((item) => {
    var option_custom = `<option value="${item.file}">${item.name}</option>`;
    return(option_custom);
  }).join("");

// Generate options for subhydrological zones
const subhyz_url = `${server}/static/historical_validation_tool_colombia/geojson/sub_hydr_zone/`;
subhyz = subhyz.map((item) => {
    var option_custom = `<option value="${item.file}">${item.name}</option>`;
    return(option_custom);
}).join("");


selbox_control = `
    <div class="control-group">

        <label class="label-control" for="select-loc">Departamento:</label>
        <select id="select-loc" required class="demo-default" placeholder="Seleccione un departamento." name="loc">
            <option value="">Seleccione un departamento.</option>
            ${loc}
        </select>
        <br>

        <label class="label-control" for="select-hyz">Zona hidrogáfica:</label>
        <select id="select-hyz" required class="demo-default" placeholder="Seleccione una zona hidrográfica." name="hyz">
            <option value="">Seleccione una zona hidrográfica.</option>
            ${hyz}
        </select>
        <br>

        <label class="label-control" for="select-subhyz">Sub Zona hidrogáfica:</label>
        <select id="select-subhyz" required class="demo-default" placeholder="Seleccione una sub zona hidrográfica." name="subhyz">
            <option value="">Seleccione una sub zona hidrográfica.</option>
            ${subhyz}
        </select>
        <br>

    </div>
`

function dynamic_select_boxes(){

    // Select box for ZOOM to localities (Provincias)
    $('#select-loc').selectize({
        create: false,
        //sortField: { field: 'text', direction: 'asc'},
        onChange: function(value, isOnInitialize) {
            // Retrieve geojson from REST API
            fetch(`${loc_url}${value}`)
            .then((response) => (layer = response.json()))
            .then((layer) => {
                // Remove the current layer
                if (typeof layerSHP !== 'undefined') {
                    map.removeLayer(layerSHP)
                }
                // Add retrieved layer and fit to map
                if(value === "COLOMBIA.geojson"){
                    layerSHP = L.geoJSON(layer, { style:  {weight: 2, fillOpacity: 0} }).addTo(map);
                }else{
                    layerSHP = L.geoJSON(layer, { style: { weight: 1 } }).addTo(map);
                }
                map.fitBounds(layerSHP.getBounds());
            });
        }
    });

    // Select box for ZOOM to to hydrological zone
    $('#select-hyz').selectize({
        create: true,
        //sortField: { field: 'text', direction: 'asc'},
        onChange: function(value, isOnInitialize) {
            // Retrieve geojson from REST API
            fetch(`${hyz_url}${value}`)
            .then((response) => (layer = response.json()))
            .then((layer) => {
                // Remove the current layer
                if (typeof layerSHP !== 'undefined') {
                    map.removeLayer(layerSHP)
                }
                // Add retrieved layer and fit to map
                if(value === "COLOMBIA.geojson"){
                    layerSHP = L.geoJSON(layer, { style:  {weight: 2, fillOpacity: 0} }).addTo(map);
                }else{
                    layerSHP = L.geoJSON(layer, { style: { weight: 1 } }).addTo(map);
                }
                map.fitBounds(layerSHP.getBounds());
            });
        }
    });


    // Select box for ZOOM to to hydrological sub zone
    $('#select-subhyz').selectize({
        create: true,
        //sortField: { field: 'text', direction: 'asc'},
        onChange: function(value, isOnInitialize) {
            // Retrieve geojson from REST API
            fetch(`${subhyz_url}${value}`)
            .then((response) => (layer = response.json()))
            .then((layer) => {
                // Remove the current layer
                if (typeof layerSHP !== 'undefined') {
                    map.removeLayer(layerSHP)
                }
                // Add retrieved layer and fit to map
                if(value === "COLOMBIA.geojson"){
                    layerSHP = L.geoJSON(layer, { style:  {weight: 2, fillOpacity: 0} }).addTo(map);
                }else{
                    layerSHP = L.geoJSON(layer, { style: { weight: 1 } }).addTo(map);
                }
                map.fitBounds(layerSHP.getBounds());
            });
        }
    });

};