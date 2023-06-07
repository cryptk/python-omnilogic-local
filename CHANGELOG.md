# Changelog

<!--next-version-placeholder-->

## v0.10.0 (2023-06-07)
### Feature
* Improve set chlor params ([#36](https://github.com/cryptk/python-omnilogic-local/issues/36)) ([`97767f3`](https://github.com/cryptk/python-omnilogic-local/commit/97767f37bf9fb8b922a6754cfbea90743e68bf25))

## v0.9.0 (2023-06-07)
### Feature
* Support chlorinator on/off switch ([#34](https://github.com/cryptk/python-omnilogic-local/issues/34)) ([`f8398d6`](https://github.com/cryptk/python-omnilogic-local/commit/f8398d6411dab181ea2e36777f2cb83cbfbb7dd1))

## v0.8.1 (2023-06-07)
### Fix
* Force pumps to always parse as a list ([#32](https://github.com/cryptk/python-omnilogic-local/issues/32)) ([`074c5e8`](https://github.com/cryptk/python-omnilogic-local/commit/074c5e82b9510e15cd711482147f095d2735ad42))

### Documentation
* Add buy me a coffee to README.md ([#31](https://github.com/cryptk/python-omnilogic-local/issues/31)) ([`9009f2c`](https://github.com/cryptk/python-omnilogic-local/commit/9009f2c5d3801ff1338cde3caf5419bd6a89162d))

## v0.8.0 (2023-05-31)
### Feature
* Some cleanup and initial work towards tests ([#30](https://github.com/cryptk/python-omnilogic-local/issues/30)) ([`37ff4a6`](https://github.com/cryptk/python-omnilogic-local/commit/37ff4a6f875c63ec6ede5dc2040e6bc68317b93e))

## v0.7.0 (2023-05-31)
### Feature
* Add pump parsing to MSPConfig ([#29](https://github.com/cryptk/python-omnilogic-local/issues/29)) ([`4f54859`](https://github.com/cryptk/python-omnilogic-local/commit/4f54859fea32a21f346434846d23a4f6d5b99304))

## v0.6.2 (2023-05-30)
### Fix
* Non-compressed, non-segmented responses were missing the first few characters ([#28](https://github.com/cryptk/python-omnilogic-local/issues/28)) ([`f1f6913`](https://github.com/cryptk/python-omnilogic-local/commit/f1f6913a322f97c059887ac5b9b9dd35abf2f928))

## v0.6.1 (2023-05-30)
### Fix
* Virtual heaters are always a list now ([#27](https://github.com/cryptk/python-omnilogic-local/issues/27)) ([`f8df720`](https://github.com/cryptk/python-omnilogic-local/commit/f8df7200630d58fc2ccb3c868b2bc3ffaf8b07a4))

## v0.6.0 (2023-05-30)
### Feature
* More improvements ([#26](https://github.com/cryptk/python-omnilogic-local/issues/26)) ([`62a4af4`](https://github.com/cryptk/python-omnilogic-local/commit/62a4af44ab5b7081d1d2c9ece9962305a98bd0a7))

## v0.5.1 (2023-05-30)
### Fix
* Cleanup message logging, allow slightly longer for ACK timeout ([#25](https://github.com/cryptk/python-omnilogic-local/issues/25)) ([`68f5fdc`](https://github.com/cryptk/python-omnilogic-local/commit/68f5fdca080cca97723467a2537a1e38185078ea))

## v0.5.0 (2023-05-30)
### Feature
* Improve logging and message retransmission behavior ([#24](https://github.com/cryptk/python-omnilogic-local/issues/24)) ([`2712c6d`](https://github.com/cryptk/python-omnilogic-local/commit/2712c6dd6102afec56d19ceddfdc81c9e69aa840))

## v0.4.2 (2023-05-29)
### Fix
* Mark v2_active field on CL lights as optional ([#21](https://github.com/cryptk/python-omnilogic-local/issues/21)) ([`fa46542`](https://github.com/cryptk/python-omnilogic-local/commit/fa4654289681e90d22fe33f32ff5c90e23a932e4))

### Documentation
* Improve lots of docstrings ([#19](https://github.com/cryptk/python-omnilogic-local/issues/19)) ([`03cc05c`](https://github.com/cryptk/python-omnilogic-local/commit/03cc05c6c521f6e734d86fc10aee5667a9f77c4e))

## v0.4.1 (2023-05-28)
### Fix
* Allow pydantic to fall back to int/str if value is not in an Enum ([#18](https://github.com/cryptk/python-omnilogic-local/issues/18)) ([`9db06b4`](https://github.com/cryptk/python-omnilogic-local/commit/9db06b4828e2623cba191c80c73ff3f7bd0804df))

## v0.4.0 (2023-05-28)
### Feature
* Add support for relays attached to backyards ([#17](https://github.com/cryptk/python-omnilogic-local/issues/17)) ([`2275ce9`](https://github.com/cryptk/python-omnilogic-local/commit/2275ce9d2920294d3873ca8326bd6ca49c8a1c0a))

## v0.3.4 (2023-05-27)
### Fix
* Add MessageType.MSP_TELEMETRY_UPDATE to _wait_for_ack to prevent deathloops ([#16](https://github.com/cryptk/python-omnilogic-local/issues/16)) ([`8a65727`](https://github.com/cryptk/python-omnilogic-local/commit/8a6572768df1a6b2fa006b74c67825f68cdc579d))

## v0.3.3 (2023-05-27)
### Fix
* Dropped acks when requesting config/telem throwing us into a death loop ([#15](https://github.com/cryptk/python-omnilogic-local/issues/15)) ([`4a4b51d`](https://github.com/cryptk/python-omnilogic-local/commit/4a4b51d76350b747464153b9f95041facc9e2a8f))

## v0.3.2 (2023-05-27)
### Fix
* Don't propagate bow_id to devices that don't exist ([#14](https://github.com/cryptk/python-omnilogic-local/issues/14)) ([`f6e518f`](https://github.com/cryptk/python-omnilogic-local/commit/f6e518ff809bbec93ec18ffa7b834e88d5e59d99))

## v0.3.1 (2023-05-27)
### Fix
* Chlorinator telemetry enable parsing ([#13](https://github.com/cryptk/python-omnilogic-local/issues/13)) ([`4efd0d8`](https://github.com/cryptk/python-omnilogic-local/commit/4efd0d89f873cf8fad97f849f29df59fa892e395))

## v0.3.0 (2023-05-27)
### Feature
* More functionality ([#12](https://github.com/cryptk/python-omnilogic-local/issues/12)) ([`20c4fa1`](https://github.com/cryptk/python-omnilogic-local/commit/20c4fa1e494b932259aff1592ea123baf5a4ea93))

## v0.2.1 (2023-05-26)
### Fix
* Correct message types for setting heater and solar temperature ([#11](https://github.com/cryptk/python-omnilogic-local/issues/11)) ([`361d6b7`](https://github.com/cryptk/python-omnilogic-local/commit/361d6b7971168d35174719d84fa196471eeb3078))

## v0.2.0 (2023-05-26)
### Feature
* Add solar set point support, fixes #9 ([#10](https://github.com/cryptk/python-omnilogic-local/issues/10)) ([`4bb1951`](https://github.com/cryptk/python-omnilogic-local/commit/4bb1951f97248cf027329934964c7f66622054ab))

## v0.1.0 (2023-05-26)
### Feature
* Fix pylint in pre-commit ([`cf8067e`](https://github.com/cryptk/python-omnilogic-local/commit/cf8067e8b62cc4de7c452135f96a7cf7be8815cb))
* Output data parsed into pydantic models ([`4e6c39d`](https://github.com/cryptk/python-omnilogic-local/commit/4e6c39da924f90ee6b2ad5f176743c35fb55fada))
* Try a different poetry action ([`7dd0ab2`](https://github.com/cryptk/python-omnilogic-local/commit/7dd0ab250f116263bff47b40f1972cc49dd1f1db))
* Disable python semantic release job ([`1d2efba`](https://github.com/cryptk/python-omnilogic-local/commit/1d2efbadc4b7bda4a7eb5feb50548021f8709b24))
* Add pytest to dependencies ([`dfabb7b`](https://github.com/cryptk/python-omnilogic-local/commit/dfabb7b5bb42965b7e5c5bf8b26d6cd93bc374da))
* Big cleanup of api and protocol code ([`f8b5207`](https://github.com/cryptk/python-omnilogic-local/commit/f8b52072d240ffe8dbf53ef172a12193b1cc472c))
* Initial version of pydantic models complete ([`0db97a8`](https://github.com/cryptk/python-omnilogic-local/commit/0db97a86ab9e8a48591b02e4b09bb4a935c94bf7))
* Initial work towards using pydantic ([`9c4b4b6`](https://github.com/cryptk/python-omnilogic-local/commit/9c4b4b6ce693796d88ec402d6e6f33f3bdc152aa))

### Fix
* Remove pylint from pre-commit for now to fix CI ([`9d07ce1`](https://github.com/cryptk/python-omnilogic-local/commit/9d07ce169c873ec927fd34caa9a24b89e5ed3ca4))
* Disable pytest until we have tests ([`f97bf34`](https://github.com/cryptk/python-omnilogic-local/commit/f97bf341458a9d9716f029b7da637d9addbd8ae6))
* Try and fix PR CI again ([`71271e4`](https://github.com/cryptk/python-omnilogic-local/commit/71271e4473bf807bdfa70e123248cb2537b0d5eb))
