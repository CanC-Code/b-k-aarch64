#ifndef BANJO_KAZOOIE_CORE2_STRING_H
#define BANJO_KAZOOIE_CORE2_STRING_H

#include <ultra64.h>

/*
 * These functions are slightly modified from the Standard C Library.
 * To avoid naming collisions and make porting easier, they were prefixed.
 */

void bk_strcat(char *dest, const char *src);
void bk_strcatc(char *dest, char src);
void bk_strFToA(char *dest, f32 val); // custom function
void bk__strFToA(char *dest, f32 val, s32 decPlaces);
void bk_strIToA(char *str, s32 num); // custom function
void bk__strIToA(char *str, s32 num, char prefix); // custom function
int bk_strcmp(const char *lhs, const char *rhs);
void bk_strcpy(char *dest, const char *src);
int bk_strlen(const char *str);
int bk_strcmptotok(char *str1, char *str2, char *str3); // custom function
char *bk_strtok(char *str, const char *delim);
void bk_strcpytotok(char *str1, char *str2, char *str3); // custom function
void bk_strupr(char *str);

#endif

