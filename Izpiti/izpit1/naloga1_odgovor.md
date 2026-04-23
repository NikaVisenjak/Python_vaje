# Izpit 1 - Naloga 1: Šifrirana komunikacija s "čudežnima" ključema C in D

## Ozadje
Imamo simetrična ključa C in D, kjer vrstni red šifriranja/dešifriranja **ni pomemben**:
- encrypt(C, encrypt(D, M)) == encrypt(D, encrypt(C, M))
- decrypt(C, decrypt(D, M)) == decrypt(D, decrypt(C, M))

## Postopek (analog Diffie-Hellman z XOR / komutativno šifro)

Recimo, da želi Alice poslati sporočilo Bobu, brez predhodnega dogovora:

1. **Alice** si ustvari lasten ključ C (samo ona ga pozna).
2. **Bob** si ustvari lasten ključ D (samo on ga pozna).
3. Alice šifrira sporočilo M s svojim ključem C → pošlje E_C(M) Bobu.
4. Bob prejme E_C(M) in ga dodatno šifrira s svojim ključem D → pošlje E_D(E_C(M)) nazaj Alici.
5. Alice dešifrira s svojim ključem C → ker vrstni red ni pomemben, dobi E_D(M) → pošlje E_D(M) Bobu.
6. Bob dešifrira z svojim ključem D → dobi M.

## Zakaj to deluje?
Ker je šifriranje **komutativno** (vrstni red ni važen):
- E_D(E_C(M)) == E_C(E_D(M))
- Torej ko Alice odstrani C iz E_D(E_C(M)), dobi E_D(M)
- Bob nato odstrani D in dobi M

## Kdaj je to varno?
Nobena stran ni nikoli razkrila svojega ključa. Napadalec na omrežju vidi:
- E_C(M)         → ne more dešifrirati brez C
- E_D(E_C(M))    → ne more dešifrirati brez C ali D
- E_D(M)         → ne more dešifrirati brez D
